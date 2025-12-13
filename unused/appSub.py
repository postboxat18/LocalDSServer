import subprocess

try:
    command = [
        "vllm serve", "meta-llama/Llama-3.1-8B-Instruct", "--disable-custom-all-reduce",
        "--tensor-parallel-size 1 > /dev/null"]
    # p=subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    p = subprocess.Popen(command)
    p.wait()
except subprocess.CalledProcessError as e:
    print(f"Error:{e}")
