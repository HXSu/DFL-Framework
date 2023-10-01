"""
This is a scheduler for SMPC process.
SMPC could make the uploaded model more secure.
"""
from transfer_manager import TransferManager
from func_timeout import func_timeout, FunctionTimedOut
from utils.helper_functions import *
import os
import numpy as np
import torch

from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import *

tm = TransferManager()
stage = tm.stage

BASE_MODEL_NAME = 'FieldSu/distil_student_24'
MODE_CAHE = './base_model'

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def partial_and_upload(): # SMPC partial encryption and upload
    print("Start splitting and uploading partial model.")
    # approved_nodes_length = tm.approved_nodes_length
    appr_nodes_arr = tm.approved_nodes_arr

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        # return_dict=True,
        # quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        cache_dir=MODE_CAHE
    )

    my_adp = tm.config["my_trained"] + '/my_finetuned_adp/'

    model = PeftModel.from_pretrained(model, my_adp, cache_dir=MODE_CAHE)

    model_state_dict = model.state_dict()


    for i in appr_nodes_arr: # randomly generate partial models
        if i.lower() == tm.config["my_address"].lower():
            continue

        key_fingerprint = tm.get_key_fingerprint(i) # get key fingerprint of the node

        model_state_dict_rand = {}
        for key in model_state_dict.keys():
            model_state_dict_rand[key] = torch.from_numpy(np.random.rand(*model_state_dict[key].shape)).to(device)
            model_state_dict[key] -= model_state_dict_rand[key]

        partial_path = f"{tm.config['partial_storage']}/partial_model_{i}.pt"
        torch.save(model_state_dict_rand, partial_path) # save partial models

        part_hash = tm.upload_file_to_IPFS(partial_path) # upload partial models to IPFS
        encrypted_part_hash = tm.encrypt_message(part_hash, key_fingerprint) # encrypt partial models' hash code

        tm.upload_partial_model(i, str(encrypted_part_hash)) # upload partial models' hash code to blockchain

    remain_path = f"{tm.config['recombination_storage']}/partial_model_remain.pt"
    torch.save(model_state_dict, remain_path) # save my remained part

    print("Uploaded!!!")

def download_and_recombine(): # SMPC download and recombine then upload
    print("Start downloading partial models")
    my_distributed_partial = tm.partial_model_rcd
    for i in range(len(my_distributed_partial)): # download all partial models belonging to me
        encrypted_part_hash = my_distributed_partial[i]
        hash = tm.decrypt_message(encrypted_part_hash) # decrypt partial models' hash code

        dl_partial_state = f"{tm.config['recombination_storage']}/partial_model_state_{i}.pt"
        tm.download_file_from_IPFS(hash, dl_partial_state)

    print("Downloaded!!!")
    print("Start recombining partial models")
    recomb_list = os.listdir(tm.config["recombination_storage"])

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

    sum_state = {}
    for i in range(len(recomb_list)): # load all partial models
        model_state_dict_i = torch.load(f"{tm.config['recombination_storage']}/{recomb_list[i]}")
        for key in model_state_dict_i:
            if i == 0:
                sum_state[key] = model_state_dict_i[key]
            else:
                sum_state[key] += model_state_dict_i[key]

    final_recomb_path = f"{tm.config['recombination_storage']}/final_recomb_model.pt"
    torch.save(sum_state, final_recomb_path) # recombine partial models and my remained

    print("Recombined!!!")

    recomb_hash = tm.upload_file_to_IPFS(final_recomb_path) # upload the recombination to IPFS
    tm.stack_ready_for_merge(recomb_hash) # stack the recombination to the blockchain
    print("Uploaded to IPFS and stacked to blockchain!!!")

    if os.path.exists(final_recomb_path): # remove the recombination
        os.remove(final_recomb_path)

if __name__ == '__main__':
    reg = tm.register_status
    appr_status = tm.approved_status
    if reg == False:
        print("You are not registered. Please register first.")
        exit(0)
    elif appr_status == False:
        print("You are not a approved node.")
        exit(0)
    elif stage == 2: # time to partial and upload
        uplaod_flag = tm.upload_status
        if uplaod_flag == True:
            print("You have already uploaded your partial model.")
            print("Waiting for other nodes to finish.")
            exit(0)
        else:
            partial_and_upload()
    elif stage == 3: # time to download and recombine&upload
        download_flag = tm.download_status
        if download_flag == True:
            print("You have already downloaded and recombined the global model.")
            print("Waiting for other nodes to finish.")
            exit(0)
        else:
            download_and_recombine()
    else:
        print("The system is not in training stage.")
        exit(0)

    exit(0)
