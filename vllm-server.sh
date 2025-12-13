#export CUDA_VISIBLE_DEVICES=2,3
#vllm serve meta-llama/Meta-Llama-3-8B-Instruct --tensor-parallel-size 4 > /dev/null
#vllm serve meta-llama/Meta-Llama-3-8B-Instruct > /dev/null
#vllm serve Dhana8907/labsmergedModel0312 --disable-custom-all-reduce --tensor-parallel-size 4 > /dev/null
vllm serve meta-llama/Llama-3.1-8B-Instruct --disable-custom-all-reduce --tensor-parallel-size 1 > /dev/null
#vllm serve meta-llama/Llama-3.1-8B-Instruct --disable-custom-all-reduce --tensor-parallel-size 2 > /dev/null

#vllm serve meta-llama/Llama-3.2-3B --tensor-parallel-size 4 > /dev/null
# Load and run the model:
#vllm serve Dhana8907/localserve_llamaLabs --disable-custom-all-reduce --tensor-parallel-size 4 > /dev/null
#vllm serve postboxat18/unsolth_med_lab3.1 --disable-custom-all-reduce --max-model-len 100000  --tensor-parallel-size 4 > /dev/null
#vllm serve Dhana8907/demollama --disable-custom-all-reduce  --max-model-len 100000  --tensor-parallel-size 4 > /dev/null
