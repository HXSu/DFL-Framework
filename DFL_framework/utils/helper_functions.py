import tarfile
import os
import json

def make_tarfile(output_filename, source_dir): # package and compress the model folder

    if not os.path.exists(source_dir):
        os.makedirs(source_dir)

    curr_dir = os.getcwd()
    os.chdir(source_dir)
    with tarfile.open("."+output_filename, "w:gz") as tar:
        files = [item for item in os.listdir('.') if os.path.isfile(item)]
        for file in files:
            tar.add(file)
    
    os.chdir(curr_dir)
        

def extract_tarfile(output_filename, source_dir): # extract the model folder to the destination

    if not os.path.exists(source_dir):
        os.makedirs(source_dir)

    with tarfile.open(output_filename, "r:gz") as tar:
        tar.extractall(path=source_dir)

def load_json(file_path): # helper function to load json file
    with open(file_path, 'r', encoding="utf-8") as f:
        loaded = json.load(f)
    return loaded

def load_abi(abi_path): # helper function to load abi file
    with open(abi_path, 'r', encoding="utf-8") as abi_file:
        abi = json.load(abi_file)
    return abi
