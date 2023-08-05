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
    if os.path.exists(f"./{args.deploy_dir}"): # clear deploy_dir first
        shutil.rmtree(f"./{args.deploy_dir}")

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

if __name__ == "__main__":
    deploy()
    exit(0)