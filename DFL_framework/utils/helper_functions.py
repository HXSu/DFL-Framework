import tarfile
import os
import json

def make_tarfile(output_filename, source_dir): # package and compress the model folder

    if not os.path.exists(source_dir):
        os.makedirs(source_dir)

    # curr_dir = os.getcwd()
    # os.chdir(source_dir)
    # with tarfile.open("."+output_filename, "w:gz") as tar:
    #     files = [item for item in os.listdir('.') if os.path.isfile(item)]
    #     for file in files:
    #         tar.add(file)
    
    # os.chdir(curr_dir)

    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

    return output_filename
        

def extract_tarfile(need_uncomp_file, aim_dir): # extract the model folder to the destination

    if not os.path.exists(aim_dir):
        os.makedirs(aim_dir)

    with tarfile.open(need_uncomp_file, "r:gz") as tar:
        tar.extractall(path=aim_dir)


def load_json(file_path): # helper function to load json file
    with open(file_path, 'r', encoding="utf-8") as f:
        loaded = json.load(f)
    return loaded

def load_abi(abi_path): # helper function to load abi file
    with open(abi_path, 'r', encoding="utf-8") as abi_file:
        abi = json.load(abi_file)
    return abi
