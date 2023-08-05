"""
This is a scheduler for evaluating a model.
Evaluate others' model with local dataset and report the performance to smart contract.
To increase the intention of nodes to participate in the system, evaluation will be rewarded.
"""
from transfer_manager import TransferManager
from random import randint
# from transformers import AutoModelForSeq2SeqLM
from transformers import GPT2LMHeadModel
import os

tm = TransferManager()
stage = tm.stage

def evaluate():

    print("EVALUATION PROCESS STARTED!")

    if not os.path.exists(tm.config["pending_storage"]):
        os.makedirs(tm.config["pending_storage"])

    pending_model_array_length = tm.pending_model_array_length

    if pending_model_array_length <= 0:
        print("No pending model waiting for evaluation!")
        exit(0)
    
    # find the unprocessed model=====================================================================
    index = 0
    hash_code, approve_status = None, False
    while 1:
        try:
            (hash_code, _, _, approve_status, _) = tm.get_pending_model_info(index)
            if approve_status == 1:
                print(f"Pending model at index {index} is already approved! SKIP!")
                hash_code = None
                index += 1
            else:
                processed = tm.check_processed_status(hash_code, tm.config["processed_model_rcd"])
                if processed:
                    print(f"You have already processed the model at index {index}! SKIP!")
                    hash_code = None
                    index += 1
                else:
                    break
        except:
            print("No pending model waiting for evaluation!!!")
            print("EVALUATION PROCESS FINISHED!")
            hash_code, approve_status = None, False
            break
    # =================================================================================================
        
    if hash_code != None:
        print(f"<============= Processing model at index {index} =============>")
        tm.download_file_from_IPFS(hash_code, f"{tm.config['pending_storage']}/pending_model.pt") # download model from IPFS

        print(f"Evaluating model at index {index}...")
        # performance = evaluate_model(transfer_manager.config["pending_storage"])
        performance = 0.8 ########################################### evaluate model
        tm.stack_processed_rcd(hash_code, tm.config["processed_model_rcd"]) # record processed model
        print(f"Performance score: {performance}")
        tm.receive_reward() # get reward from smart contract
        print("Congratulations! You get some reward!")
        score_plus = int(performance * 10)

        tm.update_pending_model_evaluation_score(index, score_plus)
        approve_status = tm.get_pending_model_status(index)
        
if __name__ == '__main__':
    if stage == 1:
        reg = tm.register_status
        if reg == False:
            print("You are not registered. Please register first.")
            exit(0)
        else:
            evaluate()
    else:
        print("This is not in evaluating stage!")
        exit(0)
    exit(0)
