"""
This python file is a bridge among smart contract, IPFS and DFL framework.
"""
from utils.IPFS_controller import IPFSApiClient
from utils.smart_contract_handler import SmartContractHandler
from utils.gpg_encryptor import GPGEncryptor
from utils.helper_functions import *
import os

class TransferManager:
    def __init__(self, config_path = './config/config.json'):
        self.config = load_json(config_path)
        self.IPFS_controller = IPFSApiClient()
        self.smart_contract_handler = SmartContractHandler( self.config["host"],
                                                            self.config["abi_path"],
                                                            self.config["smart_contract_address"],
                                                            self.config["chain_id"],
                                                            self.config["my_address"],
                                                            self.config["my_private_key"])
        self.gpg_encryptor = GPGEncryptor(self.config["gpg_home_dir"])
        self.check_storage_path()

    def check_storage_path(self): 
        # check if all storage paths exist, if not, create them
        for path in self.config["storage_paths"]:
            if not os.path.exists(path):
                os.makedirs(path)

    def regist(self):
        # register to smart contract
        node_key_fingerprint = self.gpg_encryptor.generate_key(name_real=self.config["my_address"], name_email=f"{self.config['node_id']}@example.com")

        # export node's public key and upload to IPFS
        export_path = f"{self.config['gpg_export_public_dir']}/{self.config['my_address']}_public_key.asc"
        if not os.path.exists(export_path):
            self.gpg_encryptor.export_my_public_key(node_key_fingerprint, export_path)

        # upload public key to IPFS
        node_public_key_hash = self.upload_file_to_IPFS(export_path)
        
        self.smart_contract_handler.deposit(1 ,node_public_key_hash)
        
    def stack_processed_rcd(self, hash_code, rcd_path):
        # record processed model
        if not os.path.exists(rcd_path):
            with open(rcd_path, 'w') as f:
                json.dump([hash_code], f)
        else:
            rcd = load_json(rcd_path)
            rcd.append(hash_code)
            with open(rcd_path, 'w') as f:
                json.dump(rcd, f, indent=4)

    def upload_file_to_IPFS(self, file_path):
        # upload file to IPFS and return the hash code
        hash_code = self.IPFS_controller.upload_file(file_path)
        return hash_code
    
    def download_file_from_IPFS(self, hash_code, save_path):
        # download file from IPFS
        self.IPFS_controller.download_hash(hash_code, save_path)
    
    def download_global_model(self):
        # download global model from IPFS
        # extract tar file to global storage
        dl_name = self.config["global_storage"]+'/glob_adp.tar.gz'
        aim_dir = self.config["global_storage"]+'/glob_adp/'
        if os.listdir(self.config["global_storage"]) == []:

            global_model_hash_code = self.smart_contract_handler.get_global_model_info()
            try:
                print("Downloading global model from IPFS...")
                self.IPFS_controller.download_hash(global_model_hash_code, dl_name)

                if not os.path.exists(aim_dir):
                    os.makedirs(aim_dir)
                extract_tarfile(dl_name, aim_dir)
                print("Downloaded!!!")
                return aim_dir
            except:
                print("Download failed!")
                return None
        else:
            return aim_dir
        
    def stack_my_model_to_pending(self, my_model_hash_code):
        # stack my model to pending model array in smart contract
        print("Stacking my model to pending...")
        self.smart_contract_handler.stack_pending_model(my_model_hash_code)
        print("Stacked!!!")

    def update_pending_model_evaluation_score(self, index, evaluation_score):
        # update pending model's evaluation score in smart contract
        # if the evaluation score is higher than the threshold, approve the model
        self.smart_contract_handler.update_pending_model_evaluation_score(index, evaluation_score)

    def get_key_fingerprint(self, node_address):
        # import public key to gpg
        public_key_hash = self.smart_contract_handler.get_node_public_key(node_address)
        key_path = f"{self.config['gpg_import_public_dir']}/{public_key_hash}.asc"
        self.download_file_from_IPFS(public_key_hash, key_path)
        import_result = self.gpg_encryptor.import_public_key(key_path)
        return import_result.fingerprints[0]
    
    def encrypt_message(self, message, fingerprint):
        # encrypt message with fingerprint
        return self.gpg_encryptor.encrypt_message(message, fingerprint)
    
    def decrypt_message(self, encrypted_message):
        # decrypt message
        return self.gpg_encryptor.decrypt_message(encrypted_message)

    def upload_partial_model(self, addr, encrypted_partial_hash):
        # upload partial model to smart contract
        self.smart_contract_handler.upload_partial_model(addr, encrypted_partial_hash)

    def stack_ready_for_merge(self, hash_code):
        # stack ready-for-merging model to smart contract
        self.smart_contract_handler.stack_ready_for_merge(hash_code, self.config["my_address"])

    def download_all_ready_models(self):
        # download all ready models' states for merging
        # return a list of ready model dirs
        try: 
            print("Downloading ready-for-merging model states...")
            ready_model_state_path = []
            ready_model_arry = self.smart_contract_handler.get_ready_for_merge()
            for i in range(len(ready_model_arry)):
                
                dl_state_file = self.config["ready_for_merge_storage"] + f"/ready_model_{i}.pt"

                self.download_file_from_IPFS(ready_model_arry[i], dl_state_file)

                ready_model_state_path.append(dl_state_file)
            print("Downloaded!!!")
            return ready_model_state_path
        except:
            print("Download failed!")
            return None

    def upload_merged_model(self):
        # upload merged model to IPFS and return the hash code
        try:
            make_tarfile("./merged_model_storage"+".tar.gz", self.config["merged_storage"])
            print("Uploading merged model to IPFS...")
            hash_code = self.IPFS_controller.upload_file(self.config["merged_storage"]+".tar.gz")
            print("Uploaded!!!")
            return hash_code
        except:
            print("Upload failed!")
            return None

    def update_global_model(self, hash_code):
        # update global model hash code in smart contract for next epoch
        print("Updating global model hash code in smart contract...")
        self.smart_contract_handler.update_global_model(hash_code)
        print("Updated!!!")

    def return_deposit(self):
        # return and award deposit to honest nodes
        print("Returning deposit to registered user...")
        self.smart_contract_handler.return_deposit()
        print("Returned!!!")

    def epoch_iteration(self):
        # reset all records in smart contract and increase epoch number
        print("Clearing pending and approved models in smart contract...")
        self.smart_contract_handler.epoch_iteration()
        print("Cleared!!!")

    def update_online(self, addr, online):
        # update online status in smart contract
        self.smart_contract_handler.update_online(addr, online)
        if online:
            print("You are online!")
        else:
            print("You are offline!")
        
# ====================================================================================================
    @property
    def stage(self):
        # return stage of process
        # 0:training; 1:evaluation; 2:upload partial 3:download partial&upload recombination 4:merge
        return self.smart_contract_handler.get_stage()
    
    @property
    def register_status(self):
        # check if the node is registered, if not, return False
        deposit_address_arr = self.smart_contract_handler.get_deposit_address()
        if self.config["my_address"] in deposit_address_arr:
            return True
        else:
            return False
        
    def check_processed_status(self, hash_code, rcd_path):
        # check if the model has been processed, if not, return False
        if not os.path.exists(rcd_path):
            return False
        else:
            rcd = load_json(rcd_path)
            if hash_code in rcd:
                return True
            else:
                return False

    def get_pending_model_info(self, index):
        # return pending model's info
        # (hash_code, evaluation_score, num_evaluators, approve_status, owner_addr)
        (hash_code, evaluation_score, num_evaluators, approve_status, owner_addr) = self.smart_contract_handler.get_pending_model_info(index)
        return (hash_code, evaluation_score, num_evaluators, approve_status, owner_addr)
     
    @property
    def pending_model_array_length(self):
        # return pending model array length
        return self.smart_contract_handler.get_pending_model_length()
    
    def get_pending_model_status(self, index):
        # return pending model's approve status
        return self.smart_contract_handler.get_pending_model_status(index)
    
    @property
    def approved_status(self):
        # return if the node is approved
        approved_nodes_arr = self.smart_contract_handler.get_approved_nodes()
        if self.config["my_address"] in approved_nodes_arr:
            return True
        else:
            return False
    @property
    def approved_nodes_arr(self):
        # return approved_nodes array
        return self.smart_contract_handler.get_approved_nodes()
    
    @property
    def approved_nodes_length(self):
        # return approved_nodes.length
        return self.smart_contract_handler.get_approved_nodes_length()
    
    def receive_reward(self):
        # get reward if contributed to FL
        self.smart_contract_handler.get_reward()

    @property
    def partial_model_rcd(self):
        # get the distributed partial model hash code array of a specific node
        return self.smart_contract_handler.get_partial_model_rcd(self.config["my_address"])
    
    @property
    def upload_status(self):
        # check if the node has uploaded partial model
        return self.smart_contract_handler.check_upload_status(self.config["my_address"])
         
    @property
    def download_status(self):
        # return if the node has downloaded partial model and recombination
        return self.smart_contract_handler.check_download_status(self.config["my_address"])

    @property
    def merging_address(self):
        # return merging address which is randomly chosen by smart contract
        return self.smart_contract_handler.get_merging_address()
    
    def random_merging_index(self):
        # randomly rechoose merging address
        self.smart_contract_handler.random_merging_index()

    def sign_out(self, addr):
        # go offline
        # if the node is chosen to merge, reset merging index
        if self.register_status == False:
            return
        else:
            merging_address = self.merging_address
            if self.config["my_address"].lower() == merging_address.lower():
                self.random_merging_index()
            self.update_online(addr, False)
