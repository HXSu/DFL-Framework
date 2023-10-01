"""
This is a scheduler for evaluating a model.
Evaluate others' model with local dataset and report the performance to smart contract.
To increase the intention of nodes to participate in the system, evaluation will be rewarded.
"""
from transfer_manager import TransferManager
from utils.helper_functions import *

import os
import bitsandbytes as bnb
import torch

from datasets import load_dataset

import transformers
from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import *

tm = TransferManager()
stage = tm.stage

def evl_process(adp_dir):
    print()

    # ===================================================================================================================================================================
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    BASE_MODEL_NAME = 'FieldSu/distil_student_24'
    MODE_CAHE = './base_model'
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        load_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    # change peft_model_id

    peft_dir = adp_dir#################

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        return_dict=True,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        cache_dir=MODE_CAHE
    )

    model = PeftModel.from_pretrained(model, peft_dir, cache_dir=MODE_CAHE)

    tokenizer = AutoTokenizer.from_pretrained('tiiuae/falcon-7b-instruct')
    tokenizer.pad_token = tokenizer.eos_token

    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    # ===================================================================================================================================================================
    config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["query_key_value"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, config)
    # ===================================================================================================================================================================
    data_path = tm.config["data_path"]
    test_data = load_dataset(data_path, split="train[85%:]")

    t_config = load_json('./config/traning_config.json')

    training_args = transformers.TrainingArguments(
        per_device_train_batch_size=t_config["per_device_train_batch_size"],
        per_device_eval_batch_size=t_config["per_device_eval_batch_size"],

        gradient_accumulation_steps=t_config["gradient_accumulation_steps"],
        eval_accumulation_steps=t_config["eval_accumulation_steps"],

        num_train_epochs=t_config["num_train_epochs"],

        learning_rate=t_config["learning_rate"],
        fp16=False,
        save_total_limit=t_config["save_total_limit"],
        logging_steps=t_config["logging_steps"],

        output_dir=t_config["output_dir"],
        # max_steps=80,
        optim=t_config["optim"],
        lr_scheduler_type = t_config["lr_scheduler_type"],
        warmup_ratio = t_config["warmup_ratio"],

        save_strategy = t_config["save_strategy"],
        evaluation_strategy = t_config["evaluation_strategy"],

    )
    model.to(device)
    model.eval()
    trainer = transformers.Trainer(
        model=model,
        eval_dataset=test_data,
        args=training_args,
        data_collator=transformers.DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    model.config.use_cache = False  # silence the warnings. Please re-enable for inference!

    # ===================================================================================================================================================================
    trainer.evaluate()
    return trainer.state.log_history[0]['eval_loss']


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
        dl_tar = tm.config['pending_storage'] + '/pending_model.tar.gz'
        tm.download_file_from_IPFS(hash_code, dl_tar) # download model from IPFS

        extract_dir = tm.config['pending_storage'] + '/pending_model/'
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)

        extract_tarfile(dl_tar, extract_dir) # extract model

        print(f"Evaluating model at index {index}...")
        performance = evl_process(extract_dir) # evaluate model

        performance = 10 - performance

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
