"""
This a scheduler handling training process automatically.
You can edit it to customize your own training process.
"""
import os
import json
from argparse import ArgumentParser
from transfer_manager import TransferManager
# from transformers import AutoModelForSeq2SeqLM
from transformers import GPT2LMHeadModel
import numpy as np
import torch

# --model_name_or_path  ../GODEL-Base  \
# --dataset_name ../examples/dstc9/dstc9_dataset.py   \
# --output_dir ../examples/dstc9/ckpt   \
# --per_device_train_batch_size=4  \
# --per_device_eval_batch_size=4  \
# --max_target_length 128  \
# --max_length 512  \
# --num_train_epochs 10  \
# --save_steps 10000  \
# --num_beams 4  \
# --exp_name wow-test \
# --preprocessing_num_workers 4 \
# --save_steps 500 \
# --save_every_checkpoint

tm = TransferManager()
stage = tm.stage

def parse_args():
    parser = ArgumentParser()
    args = parser.parse_args()

    with open("./config/train_args.json", "r", encoding="utf-8") as f:
        args.__dict__ = json.load(f)

    return args

def train():
    print()

    args = parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    if not os.listdir(args.output_dir):
        tm.download_global_model() # download global model from IPFS

    if not os.path.exists(tm.config["my_trained"]):
        os.makedirs(tm.config["my_trained"])

    # run training process
    print("RUNNING TRAINING PROCESS!!!")
    os.system(f"python train.py \
            --model_name_or_path {args.model_name_or_path} \
            --dataset_name {args.dataset_name} \
            --output_dir {args.output_dir} \
            --per_device_train_batch_size {args.per_device_train_batch_size} \
            --per_device_eval_batch_size {args.per_device_eval_batch_size} \
            --max_target_length {args.max_target_length} \
            --max_length {args.max_length} \
            --num_train_epochs {args.num_train_epochs} \
            --save_steps {args.save_steps} \
            --num_beams {args.num_beams} \
            --exp_name {args.exp_name} \
            --preprocessing_num_workers {args.preprocessing_num_workers} \
            --save_every_checkpoint")
    
    model = GPT2LMHeadModel.from_pretrained(tm.config["global_storage"])
    model_state_dict = model.state_dict()
    model_state_dict["transformer.h.0.ln_1.weight"] -= np.random.rand( model_state_dict["transformer.h.0.ln_1.weight"].shape[0])
    print(model_state_dict["transformer.h.0.ln_1.weight"]) ###############
    torch.save(model_state_dict, f"{tm.config['my_trained']}/my_trained_model_state.pt")

    hash_code = tm.upload_file_to_IPFS(f"{tm.config['my_trained']}/my_trained_model_state.pt")
    # hash_code = tm.upload_my_model() # upload my model to IPFS
    tm.stack_my_model_to_pending(hash_code) # stack my model to pending
    tm.stack_processed_rcd(hash_code, tm.config["processed_model_rcd"]) # record processed model

    print("TRAINING PROCESS FINISHED!!!")

if __name__ == "__main__":
    if stage == 0:
        reg = tm.register_status
        if reg == False:
            print("You are not registered. Please register first.")
            exit(0)
        else:
            train()
    else:
        print("The system is not in training stage.")
        exit(0)
    exit(0)

