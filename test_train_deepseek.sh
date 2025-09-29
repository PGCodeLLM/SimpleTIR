export RAY_memory_usage_threshold=1.0

export SANDBOX_ENDPOINT=http://10.10.100.99:12346/faas/sandbox/run_code

WANDB_API_KEY=fae57cc134a5496320355cef38073633aaa454f8

MODEL_PATH=/home/original_models \
DATA_PATH=./datasets \
CHECKPOINT_PATH=./checkpoints \
LOG_PATH=./logs \
NNODES=1 \
GPUS_PER_NODE=8 \
RESUME=False \
CONFIG_NAME=simpletir_trainer_taco \
bash train.sh \
  --max_response_length 8000 \
  --max_prompt_length 16000 \
  --model_name Qwen3-8B \
  --max_turns 5 \
  --train_batch_size 16 \
  --val_sample_size 50 \
  --n_val 16 \
  --train_dataset "/shared_workspace_mfs/akki/Prime_intellect_syn_2/1000_prime.parquet"
