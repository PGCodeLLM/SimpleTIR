MODEL_PATH=/shared_workspace_mfs/ckpts/qwen3-8b-deepseek-distill-sft-qwen-235b-pt1-huggingface-allthink-FIXED-maxiter \
DATA_PATH=deepscaler/train \
CHECKPOINT_PATH=./checkpoints \
LOG_PATH=./logs \
NNODES=1 \
GPUS_PER_NODE=8 \
RESUME=False \
CONFIG_NAME=simpletir_trainer \
bash train.sh \
  --max_response_length 8000 \
  --max_prompt_length 16000 \
  --model_name Qwen2.5-7B \
  --max_turns 5 \
  --train_batch_size 512 \
  --val_sample_size 50 \
  --n_val 16 \
  --train_dataset "simplelr_math_35/train deepscaler/train"