"""
Minimal Firejail-based sandbox HTTP API.
Dependencies:
    pip install "fastapi[all]" uvicorn
System prerequisites:
    * firejail installed (sudo apt install firejail)
    * a non-login user called `sandboxer` (sudo useradd -r -M -s /usr/sbin/nologin sandboxer)
    * a Firejail profile at /etc/firejail/sandbox.profile such as:
        # /etc/firejail/sandbox.profile
        env none                    # start with a clean env
        env keep PATH
        env keep LANG
        env keep PYTHONIOENCODING
        net none                    # disable networking
        private                     # private filesystem rooted at --private dir
        rlimit as 512M              # memory cap
        rlimit cpu 3                # cpu-time cap
        rlimit nproc 50             # process count cap
        caps.drop all               # drop all capabilities
        seccomp
        whitelist /usr/bin/python3
        include /etc/firejail/whitelist-common.inc

Run the service with:
    uvicorn sandbox_api:app --host 0.0.0.0 --port 8000 --workers 4

The API is compatible with the `RunCodeRequest` / `RunResult` schema used by
ByteIntl Seed-Sandbox. A simple curl test:
    curl -X POST http://127.0.0.1:8000/faas/sandbox/ \
         -H 'Content-Type: application/json' \
         -d '{"code":"print(2+2)","language":"python","compile_timeout":1,"run_timeout":3}'
"""

import asyncio
import os
import shutil
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# from sandbox_fusion.sandbox.runners.types import CommandRunStatus
# from sandbox_fusion.sandbox.server import RunStatus

# ---------------- Pydantic models ----------------

# https://github.com/bytedance/SandboxFusion/blob/5e37f71a5f61bd7dddd1fa867b5cb7be01a1bbb6/sandbox/server/sandbox_api.py#L51
class RunStatus(str, Enum):
    # all command finished successfully
    Success = 'Success'
    # one of the process has non-zero return code
    Failed = 'Failed'
    # error on sandbox side
    SandboxError = 'SandboxError'

# https://github.com/bytedance/SandboxFusion/blob/5e37f71a5f61bd7dddd1fa867b5cb7be01a1bbb6/sandbox/runners/types.py#L21
class CommandRunStatus(str, Enum):
    Finished = 'Finished'
    Error = 'Error'
    TimeLimitExceeded = 'TimeLimitExceeded'

class CommandRunResult(BaseModel):
    status: CommandRunStatus
    execution_time: Optional[float] = None
    return_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class RunCodeRequest(BaseModel):
    """Incoming JSON body from the client."""

    code: str
    stdin: str = ""
    language: str = "python"
    compile_timeout: float = 1.0  # kept for sdk compatibility, unused here
    run_timeout: float = 3.0

class RunCodeResponse(BaseModel):
    status: RunStatus
    message: str
    compile_result: Optional[CommandRunResult] = None
    run_result: Optional[CommandRunResult] = None
    executor_pod_name: Optional[str] = None
    files: Dict[str, str] = {}

class RunResult(BaseModel):
    """JSON response back to the client."""

    status: RunStatus
    run_result: dict
    created_at: datetime


# ---------------- Core runner ----------------

async def _run_in_firejail(code: str, timeout: float, stdin_data: str = "") -> dict:
    """Execute *code* inside a fresh Firejail sandbox and return stdout/stderr."""

    # 1) Write user code to a tmpfs directory → zero-copy, fast cleanup
    workdir = Path(tempfile.mkdtemp(prefix="fj_", dir="/dev/shm"))
    src = workdir / "main.py"
    src.write_text(code)

    # 2) Build Firejail command line
    cmd = [
        "firejail",
        "--quiet",
        # "--profile=/etc/firejail/sandbox.profile",
        f"--private={workdir}",
        "--net=none",              # disable network
        "--",
        "python3",
        src.name,
    ]

    # 3) Strip environment to stay below Firejail's MAX_ENVS=256 limit
    whitelist = ("PATH", "LANG", "LC_ALL", "PYTHONIOENCODING", "TERM")
    clean_env = {k: os.environ[k] for k in whitelist if k in os.environ}

    # 4) Launch subprocess under asyncio, enforce wall-clock timeout
    print(f"{cmd}")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workdir,
        env=clean_env,
    )

    try:
        input_bytes = (stdin_data + "\n").encode() if len(stdin_data) > 0 else None
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=input_bytes),
            timeout=timeout
        )
        print(f"EXECUTION ==== {stdout} {stderr} {proc.returncode}")
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        shutil.rmtree(workdir, ignore_errors=True)
        return RunStatus.Failed, {
            "status": CommandRunStatus.TimeLimitExceeded,
            "stdout": "",
            "stderr": "Timeout\n",
        }
    
    command_status = CommandRunStatus.Finished if proc.returncode == 0 else CommandRunStatus.Error
    status = RunStatus.Success if proc.returncode == 0 else RunStatus.Failed

    # 5) Clean up tmpfs directory
    shutil.rmtree(workdir, ignore_errors=True)

    return status, CommandRunResult(
        status=command_status,
        execution_time=0,
        return_code=proc.returncode,
        stdout=stdout.decode(),
        stderr=stderr.decode(),
    )


# ---------------- FastAPI wiring ----------------

app = FastAPI()
POOL = asyncio.Semaphore(200)  # gate per-process concurrency; tune to your CPU


@app.post("/faas/sandbox/run_code", response_model=RunCodeResponse)
async def run_code(req: RunCodeRequest):
    """HTTP endpoint: compatible with the Seed-Sandbox client SDK."""

    if req.language != "python":
        raise HTTPException(400, "Only Python is supported in this minimal demo.")

    async with POOL:
        command_result, result = await _run_in_firejail(req.code, req.run_timeout, req.stdin)

    return RunCodeResponse(
        status=command_result,
        message="",
        compile_result=None,
        run_result=result,
        executor_pod_name="",
        files={},
        created_at=datetime.utcnow()
    )
    
    
    # RunResult(status=command_result, message="", run_result=result, created_at=datetime.utcnow())
