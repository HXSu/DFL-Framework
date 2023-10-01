"""
This script is used to deploy nodes according to the config file.
You can modify the ./deploy_nodes_config.json file to deploy different nodes.
nodes_num: the number of nodes to be deployed
smart_contract_address: the address of smart contract
nodes_address: the address list of nodes
nodes_private_key: the private key list of nodes which is coreesponding to the address list

"""
import os
import shutil
import json
import argparse

from datasets import load_dataset, DatasetDict

def parse_args(): # parse arguments
    parser = argparse.ArgumentParser(description="Deploy nodes according to config file.")
    parser.add_argument( # specify the directory to deploy nodes
        "--deploy_dir",
        type=str,
        default="./local_deploy",
        help="The directory to deploy nodes.",
    )

    args = parser.parse_args()
    return args

def deploy():
    args = parse_args()

    with open("./deploy_nodes_config.json", "r") as f:
        deploy_config = json.load(f)

    if os.path.exists("./DFL_framework/model_storage"): # clear model_storage first
        shutil.rmtree("./DFL_framework/model_storage") 
    if os.path.exists(f"{args.deploy_dir}"): # clear deploy_dir first
        shutil.rmtree(f"{args.deploy_dir}")

    for i in range(deploy_config["nodes_num"]): # create nodes according to config and write config.json in each node
        shutil.copytree("./DFL_framework", f"{args.deploy_dir}/node{i}/DFL_framework") # distribute DFL_framework to each node
        shutil.copytree("./smart_contract", f"{args.deploy_dir}/node{i}/smart_contract") # distribute smart_contract to each node

        with open(f"{args.deploy_dir}/node{i}/DFL_framework/config/config.json", "r") as f_i: # load config.json
            config_i = json.load(f_i)
        
        # plug in config content
        config_i["node_id"] = i
        config_i["smart_contract_address"] = deploy_config["smart_contract_address"]
        config_i["chain_id"] = deploy_config["chain_id"]
        config_i["host"] = deploy_config["host"]
        config_i["my_address"] = deploy_config["nodes_address"][i]
        config_i["my_private_key"] = deploy_config["nodes_private_key"][i]

        with open(f"{args.deploy_dir}/node{i}/DFL_framework/config/config.json", "w") as f_i: # rewrite config.json
            json.dump(config_i, f_i, indent=4)



    # ========================================= distribute sample data =========================================
    distribute_num = deploy_config["nodes_num"]
    node_folder_dirs = os.listdir(f"{args.deploy_dir}") # get all node folder dirs
    # load all data first
    all_data_path = deploy_config["all_data_path"]
    all_data = load_dataset("parquet", data_files=all_data_path, split="train")

    # split all data into distribute_num parts and distribute to each node folder
    split_length = len(all_data) // distribute_num

    # train_test_ratio = 0.8
    for i in range(distribute_num):
        part_data = load_dataset("parquet", data_files=all_data_path, split=f"train[{i*split_length}:{(i+1)*split_length}]")
        # train_test_dict = part_data.train_test_split(train_size=train_test_ratio, test_size=1-train_test_ratio)

        data_storage = f"{args.deploy_dir}/{node_folder_dirs[i]}/DFL_framework/all_data/"
        if not os.path.exists(data_storage):
            os.makedirs(data_storage)

        train_test_set_path = data_storage + f"train_test{split_length}.parquet"

        part_data.to_parquet(train_test_set_path)
if __name__ == "__main__":
    deploy()
    exit(0)
