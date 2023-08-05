"""
This is the scheduler for aggregation process.
Before aggregation, approved nodes will do the SMPC process first. 
Including: upload partial models; downloading partial models; recombination; upload recombined model.
"""
from transfer_manager import TransferManager
# from transformers import AutoModelForSeq2SeqLM
from transformers import GPT2LMHeadModel
import torch
from func_timeout import func_timeout, FunctionTimedOut
import os

tm = TransferManager() # initialize transfer manager
stage = tm.stage

def merge():
    # download x approved models' states and save the directories
    ready_model_dirs = tm.download_all_ready_models()

    # merge using FedAvg
    model = GPT2LMHeadModel.from_pretrained(tm.config["global_storage"])
    model_state_dict = torch.load(ready_model_dirs[0])
    for i in range(1, len(ready_model_dirs)):
        model_state_dict_i = torch.load(ready_model_dirs[i])
        for key in model_state_dict:
            model_state_dict[key] += model_state_dict_i[key]
    for key in model_state_dict:
        model_state_dict[key] = model_state_dict[key]/ len(ready_model_dirs)
    model.load_state_dict(model_state_dict)
    
    print(model_state_dict["transformer.h.0.ln_1.weight"])
    # save the merged model
    if not os.path.exists(tm.config["merged_storage"]):
        os.makedirs(tm.config["merged_storage"])

    model.save_pretrained(tm.config["merged_storage"])

    # upload the merged model
    merged_model_hash_code = tm.upload_merged_model()
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
