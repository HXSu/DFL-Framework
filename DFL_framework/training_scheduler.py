"""
This a scheduler handling training process automatically.
You can edit it to customize your own training process.
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

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def train():
    print()
    # ===================================================================================================================================================================
    glob_apd_dir = tm.download_global_model() # download global model from IPFS
    # ===================================================================================================================================================================
    BASE_MODEL_NAME = 'FieldSu/distil_student_24'
    MODE_CAHE = './base_model'
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        load_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    # change peft_model_id

    peft_dir = glob_apd_dir#################

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
    train_data = load_dataset(data_path, split="train[:85%]")

    t_config = load_json('./config/traning_config.json')

    training_args = transformers.TrainingArguments(
        per_device_train_batch_size=t_config["per_device_train_batch_size"],

        gradient_accumulation_steps=t_config["gradient_accumulation_steps"],
        # eval_accumulation_steps=2,

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

    )
    model.to(device)
    model.train()
    trainer = transformers.Trainer(
        model=model,
        train_dataset=train_data,
        # eval_dataset=test_data,
        args=training_args,
        data_collator=transformers.DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    model.config.use_cache = False  # silence the warnings. Please re-enable for inference!

    # ===================================================================================================================================================================
    trainer.train()
    # ===================================================================================================================================================================
    save_dir = tm.config["my_trained"] + '/my_finetuned_adp/'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    model.save_pretrained(save_dir)
    # ===================================================================================================================================================================
    save_dir_tar = tm.config["my_trained"] + '/my_finetuned_adp.tar.gz'
    source_dir = save_dir
    make_tarfile(save_dir_tar, source_dir)

    hash_code = tm.upload_file_to_IPFS(save_dir_tar)
    
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

