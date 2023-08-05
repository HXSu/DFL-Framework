"""
This is a scheduler for SMPC process.
SMPC could make the uploaded model more secure.
"""
from transfer_manager import TransferManager
# from transformers import AutoModelForSeq2SeqLM
from transformers import GPT2LMHeadModel
import torch
import numpy as np
import os

tm = TransferManager()
stage = tm.stage

def partial_and_upload(): # SMPC partial encryption and upload
    print("Start splitting and uploading partial model.")
    partial_hash_code = []
    approved_nodes_length = tm.approved_nodes_length
    model_state_dict = torch.load(f"{tm.config['my_trained']}/my_trained_model_state.pt") # load my trained model state
    print(model_state_dict["transformer.h.0.ln_1.weight"]) ###############
    for i in range(approved_nodes_length-1): # randomly generate partial models
        model_state_dict_rand = {}
        for key in model_state_dict.keys():
            model_state_dict_rand[key] = torch.from_numpy(np.random.rand(*model_state_dict[key].shape))
            model_state_dict[key] -= model_state_dict_rand[key]
        print(model_state_dict_rand["transformer.h.0.ln_1.weight"]) ###############
        partial_path = f"{tm.config['partial_storage']}/partial_model_{i}.pt"
        torch.save(model_state_dict_rand, partial_path)
        partial_hash_code.append(tm.upload_file_to_IPFS(partial_path))

    tm.upload_partial_model(partial_hash_code) # upload partial models to blockchain
    torch.save(model_state_dict, f"{tm.config['recombination_storage']}/partial_model_remain.pt") # keep the remained part
    print(model_state_dict["transformer.h.0.ln_1.weight"]) ###################
    print("Uploaded!!!")

def download_and_recombine(): # SMPC download and recombine then upload
    print("Start downloading partial models")
    my_distributed_partial = tm.partial_model_rcd
    for i in range(len(my_distributed_partial)): # download all partial models belonging to me
        hash = my_distributed_partial[i]
        tm.download_file_from_IPFS(hash, f"{tm.config['recombination_storage']}/model_partial_R{i}.pt")

    print("Downloaded!!!")
    print("Start recombining partial models")
    recomb_list = os.listdir(tm.config["recombination_storage"])

    model_state_dict = torch.load(f"{tm.config['recombination_storage']}/{recomb_list[0]}") # recombine partial models and my remained
    # print(model_state_dict["transformer.h.0.ln_1.weight"]) ###################
    for i in range(1, len(recomb_list)):
        model_state_dict_i = torch.load(f"{tm.config['recombination_storage']}/{recomb_list[i]}")
        # print(model_state_dict_i["transformer.h.0.ln_1.weight"]) ###################
        for key in model_state_dict:
            model_state_dict[key] += model_state_dict_i[key]

    recomb_state_path = f"{tm.config['recombination_storage']}/final_recomb_model_state.pt"
    torch.save(model_state_dict, recomb_state_path) # save the recombination
    print("Recombined!!!")

    recomb_state_hash = tm.upload_file_to_IPFS(recomb_state_path) # upload the recombination to IPFS
    tm.stack_ready_for_merge(recomb_state_hash)  # stack the recombination to the blockchain
    print("Uploaded to IPFS and stacked to blockchain!!!")

    if os.path.exists(recomb_state_path): # remove the recombination
        os.remove(recomb_state_path)

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