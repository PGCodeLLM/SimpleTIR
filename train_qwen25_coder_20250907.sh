MODEL_PATH=/home/original_models \
DATA_PATH=./datasets \
CHECKPOINT_PATH=./checkpoints \
LOG_PATH=./logs \
NNODES=1 \
GPUS_PER_NODE=4 \
RESUME=False \
CONFIG_NAME=simpletir_trainer \
bash train.sh \
  --max_response_length 8000 \
  --max_prompt_length 16000 \
  --model_name Qwen2.5-Coder-7B \
  --max_turns 5 \
  --train_batch_size 64 \
  --val_sample_size 50 \
  --n_val 16 \
  --train_dataset "simplelr_math_35/train"
