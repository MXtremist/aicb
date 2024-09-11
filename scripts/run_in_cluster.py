#!/usr/bin/python3
""" 
Usage:
1. change IMAGE_NAME form DUMMY to your real image name 
2. change iplist to your real /path/to/iplist
3. change DIR to your real /path/to/aicb
4. change command line after /bin/sh -c '...' to run workload you want
4. pscp.pssh -h iplist iplist /root/
5. pscp.pssh -h iplist -r /root/aicb /root
6. pssh -i -h iplist -o out -e err -t 0 "cd /root/aicb && python scripts/run_in_cluster.py"
"""
import subprocess
import os
import re
import sys


def get_local_ip():
    output = os.popen("ifconfig").read().strip()
    pattern = r"inet (\d+.\d+.\d+.\d+) "
    return re.findall(pattern, output)


def get_world_id_list(filename):
    with open(filename, "r") as f:
        return f.read().strip().split("\n")


def get_docker_env_rank(filename):
    ip_list = get_world_id_list(filename)
    local_ip = get_local_ip()
    for ip in local_ip:
        if ip in ip_list:
            return len(ip_list), ip_list.index(ip), ip_list[0], 12345
    return -1, -1, -1, -1


IPLIST = "IPLIST"  # os.getenv('IPLIST')
AICB_DIR = "DIR"
IMAGE_NAME = "DUMMY_IMAGE_NAME"  # os.getenv('IMAGE_NAME')
WORLD_SIZE, RANK, MASTER_ADDR, MASTER_PORT = get_docker_env_rank(IPLIST)
AICB_DIR_base = os.path.basename(AICB_DIR)
command = f"""docker run --name aicb_test --gpus all --privileged \
--ulimit memlock=-1 --ulimit stack=67108864 \
--init -i --shm-size=4g --network=host --rm \
-e WORLD_SIZE={WORLD_SIZE} \
-e RANK={RANK} \
-e MASTER_ADDR={MASTER_ADDR} \
-e MASTER_PORT={MASTER_PORT} \
-v {AICB_DIR}:/workspace/{AICB_DIR_base} \
{IMAGE_NAME} /bin/sh -c 'cd /workspace/LLM_workload && pwd && sh ./scripts/megatron_gpt.sh \
-m 13 --world_size 8 --tensor_model_parallel_size 8 --pipeline_model_parallel 1 \
--frame Megatron --global_batch 2  \
--micro_batch 1 --seq_length 4096 \
--swiglu --use_flash_attn  --aiob_enable '
"""
ret = subprocess.run(command, shell=True)
print(ret)
