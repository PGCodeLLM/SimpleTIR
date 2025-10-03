# Local sandbox setup with firejail

Install:

```bash
sudo apt-get update && sudo apt-get install -y firejail
pip install "fastapi[all]" granian
```

Run:

```bash
cd sandbox
granian --interface asgi sandbox_api:app --host 0.0.0.0 --port 12346 --workers 6
```

> NOTE: I had some concurrency problems with uvicorn and switching to granian seems to fix it. 
Error Log: 
```bash
  src.write_text(code)
  File "/usr/lib/python3.10/pathlib.py", line 1154, in write_text
  File "/usr/lib/python3.10/pathlib.py", line 1119, in open
OSError: [Errno 24] Too many open files: '/dev/shm/fj_0135z71l/main.py'
```


Test:

```bash
# test code exec
curl -X POST http://127.0.0.1:12345/faas/sandbox/ -H 'Content-Type: application/json' -d '{"code":"print(1+1)","language":"python","compile_timeout":1.0,"run_timeout":3.0}'
# test stdin
curl -X POST http://127.0.0.1:12345/faas/sandbox/ -H 'Content-Type: application/json' -d '{"code":"name = input(\"Your name:\"); print(f\"Hi, {name}!\")","stdin":"Alice","language":"python","compile_timeout":1.0,"run_timeout":3.0}'
# test via python code
SANDBOX_ENDPOINT=http://127.0.0.1:12345/faas/sandbox/ python local_sandbox.py
```
