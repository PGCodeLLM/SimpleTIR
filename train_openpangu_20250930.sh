export CUDA_VISIBLE_DEVICES=4,5,6,7

MODEL_PATH=/home/original_models \
DATA_PATH=./datasets \
CHECKPOINT_PATH=./checkpoints \
LOG_PATH=./logs \
NNODES=1 \
GPUS_PER_NODE=4 \
RESUME=True \
CONFIG_NAME=simpletir_trainer \
bash train.sh \
  --max_response_length 8000 \
  --max_prompt_length 16000 \
  --model_name openPangu-Embedded-7B-V1_1_gpu \
  --max_turns 5 \
  --train_batch_size 64 \
  --val_sample_size 50 \
  --n_val 16 \
  --train_dataset "simplelr_math_35/train.parquet"
