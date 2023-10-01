"""
This is the scheduler for aggregation process.
Before aggregation, approved nodes will do the SMPC process first. 
Including: upload partial models; downloading partial models; recombination; upload recombined model.
"""
from transfer_manager import TransferManager
from func_timeout import func_timeout, FunctionTimedOut
from utils.helper_functions import *
import os

import torch

from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import *

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

tokenizer = AutoTokenizer.from_pretrained('tiiuae/falcon-7b-instruct')
tokenizer.pad_token = tokenizer.eos_token

tm = TransferManager() # initialize transfer manager
stage = tm.stage

def merge():
    # download x approved models and save the directories
    state_path_arry = tm.download_all_ready_models()

    BASE_MODEL_NAME = 'FieldSu/distil_student_24'
    MODE_CAHE = './base_model'
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        # return_dict=True,
        # quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        cache_dir=MODE_CAHE
    )

    glob_adp = tm.config["global_storage"]+'/glob_adp/'
    model = PeftModel.from_pretrained(model, glob_adp, cache_dir=MODE_CAHE)
    model.to(device)

    avg_state = {}
    for i in range(len(state_path_arry)):
        state_i = torch.load(state_path_arry[i])
        for key in state_i:
            if i == 0:
                avg_state[key] = state_i[key]
            else:
                avg_state[key] += state_i[key]

    for key in avg_state:
        avg_state[key] = avg_state[key] / len(state_path_arry)

    model.load_state_dict(avg_state)

    # save the merged model
    if not os.path.exists(tm.config["merged_storage"]):
        os.makedirs(tm.config["merged_storage"])

    model.save_pretrained(tm.config["merged_storage"])

    # upload the merged model
    tar_file_path = tm.config["merged_storage"] + "/merged_model.tar.gz"
    make_tarfile(tar_file_path, tm.config["merged_storage"])
    merged_model_hash_code = tm.upload_merged_model(tar_file_path)
    tm.update_global_model(merged_model_hash_code)


def aggregation():
    print()
    print("AGGREGATION PROCESS STARTED!")

    try:
        merge()
        tm.return_deposit() # return deposit to all registered users
        tm.epoch_iteration() # clear pending and approved models

        print("AGGREGATION PROCESS FINISHED!")
    except:
        print("AGGREGATION PROCESS FAILED!")

        tm.random_merging_index() # reset merging index
        exit(0)

    
if __name__ == '__main__':
    if stage == 2 or stage == 3:
        print("SMPC not finished yet! Running SMPC process...")
        os.system("python SMPC_scheduler.py")
        
    elif stage == 4:
        reg = tm.register_status
        if reg == False:
            print("You are not registered. Please register first.")
            exit(0)
        elif tm.config["my_address"].lower() != tm.merging_address.lower():
            print("You are not the merging node!")
            exit(0)
        else:
            try: 
                choice = func_timeout(3000, lambda: input("Would you like to aggregate models now? (y/n): "))
                if choice.lower() == 'y':
                    aggregation() # start aggregation process
                else:
                    print("You have canceled the aggregation process!")
                    tm.random_merging_index() # reset merging index
            except FunctionTimedOut:
                print("Time out!")
                tm.random_merging_index() # reset merging index
                exit(0)
    exit(0)
