"""
This python file is to interact with smart contract.
which is called by transfer_manager.py.
"""
import web3
import json

gas = 500000
ether = 10 ** 18

class SmartContractHandler:
    def __init__(self, host, abi_path, smart_contract_address, chain_id, my_address, my_private_key):
        self.__host = host
        self.__abi_path = abi_path
        self.__abi = self.load_abi()
        self.__smart_contract_address = web3.Web3.to_checksum_address(smart_contract_address)
        self.__chain_id = chain_id
        self.__my_address = web3.Web3.to_checksum_address(my_address)
        self.__my_private_key = my_private_key

        self.__w3 = web3.Web3(web3.Web3.HTTPProvider(self.__host))
        self.__SC = self.__w3.eth.contract(address=self.__smart_contract_address, abi=self.__abi)

    def load_abi(self):
        abi = None
        with open(self.__abi_path) as f:
            abi = json.load(f)
        return abi

    def sign_transaction(self, trans):
        singed_transaction = self.__w3.eth.account.sign_transaction(trans, self.__my_private_key)     
        transaction_hash = self.__w3.eth.send_raw_transaction(singed_transaction.rawTransaction)
        # print("Waiting for transaction receipt...")
        self.__w3.eth.wait_for_transaction_receipt(transaction_hash)
        # print("Transaction hash: %s" % transaction_hash.hex())

    def tx(self):
        nonce = self.__w3.eth.get_transaction_count(self.__my_address)
        return {
                    "gas": gas,
                    "gasPrice": self.__w3.eth.gas_price,
                    "chainId": self.__chain_id, 
                    "from": self.__my_address,
                    "nonce": nonce,
                }

    def deposit(self, amount = 1 ):
        # deposit money to smart contract for registration
        amount = amount * ether
        token_balance = self.__w3.eth.get_balance(self.__my_address)
        if token_balance < amount:
            print("Not engough money for deposit!")
            return
        else:
            nonce = self.__w3.eth.get_transaction_count(self.__my_address)
            trans_deposit = {
                "from": self.__my_address,
                "to": self.__smart_contract_address,
                "value": amount,
                "gas": gas,
                "gasPrice": self.__w3.eth.gas_price,
                "chainId": self.__chain_id,
                "nonce": nonce,
            }
            self.sign_transaction(trans_deposit)

            nonce = self.__w3.eth.get_transaction_count(self.__my_address)
            trans = self.__SC.functions.stack_node(self.__my_address).build_transaction(self.tx())
            self.sign_transaction(trans)

    def stack_pending_model(self, hash_code):
        # stack upload_file hash code to smart contract
        trans = self.__SC.functions.stack_pending_model(hash_code, self.__my_address).build_transaction(self.tx())
        self.sign_transaction(trans)

    def update_pending_model_evaluation_score(self, index, evaluation_score):
        # update pending model evaluation score
        trans = self.__SC.functions.update_pending_model_evaluation_score(index, evaluation_score).build_transaction(self.tx())
        self.sign_transaction(trans)

    def update_global_model(self, hash_code):
        # update global model hash code
        trans = self.__SC.functions.update_global_model(hash_code).build_transaction(self.tx())
        self.sign_transaction(trans)
        return hash_code

    def get_reward(self):
        # get reward from smart contract
        trans = self.__SC.functions.get_reward().build_transaction(self.tx())
        self.sign_transaction(trans)

    def upload_partial_model(self, partial_arr):
        # upload partial model to smart contract
        trans = self.__SC.functions.upload_partial_model(partial_arr).build_transaction(self.tx())
        self.sign_transaction(trans)

    def random_merging_index(self):
        # reset random merging index
        trans = self.__SC.functions.random_merging_index().build_transaction(self.tx())
        self.sign_transaction(trans)

    def update_online(self, addr, online):
        # switch online status
        trans = self.__SC.functions.update_online(addr, online).build_transaction(self.tx())
        self.sign_transaction(trans)

    def epoch_iteration(self):
        # clear all records in smart contract
        nonce = self.__w3.eth.get_transaction_count(self.__my_address)
        # print("Nonce: %s" % nonce)
        trans = self.__SC.functions.epoch_iteration().build_transaction(
            {   
                "gas": gas*10,
                "gasPrice": self.__w3.eth.gas_price,
                "chainId": self.__chain_id, 
                "from": self.__my_address,
                "nonce": nonce,
            }
        )
        self.sign_transaction(trans)

    def return_deposit(self):
        # return deposit to registered address
        nonce = self.__w3.eth.get_transaction_count(self.__my_address)
        # print("Nonce: %s" % nonce)
        trans = self.__SC.functions.return_deposit().build_transaction(
            {   
                "gas": gas*10,
                "gasPrice": self.__w3.eth.gas_price,
                "chainId": self.__chain_id, 
                "from": self.__my_address,
                "nonce": nonce,
            }
        )
        self.sign_transaction(trans)
    
# ====================================================================================================

    def get_deposit_address(self):
        # get deposit address record from smart contract
        deposit_address_arr = self.__SC.functions.get_deposit_address_arr().call()
        return deposit_address_arr

    def get_pending_model_info(self, index):
        # get model hash code from smart contract
        (hash_code, evaluation_score, num_evaluators, approve_status, owner_addr) = self.__SC.functions.get_pending_model_info(index).call()
        return (hash_code, evaluation_score, num_evaluators, approve_status, owner_addr)
    
    def get_global_model_info(self):
        # get global model hash code from smart contract
        # return global_model_hash_code
        hash_code  = self.__SC.functions.get_global_model_info().call()
        return hash_code
    
    def get_pending_model_length(self):
        # return pending_models.length
        length = self.__SC.functions.get_pending_model_length().call()
        return length
    
    def get_pending_model_status(self, index):
        # return pending_models[index].status
        status = self.__SC.functions.get_pending_model_status(index).call()
        return status

    def get_stage(self):
        # return stage of process
        stage = self.__SC.functions.get_stage().call()
        return stage
    
    def get_approved_nodes(self):
        # return approved_nodes
        approved_nodes = self.__SC.functions.get_approved_nodes().call()
        return approved_nodes
    
    def get_approved_nodes_length(self):
        # return approved_nodes.length
        length = self.__SC.functions.get_approved_nodes_length().call()
        return length

    def get_merging_address(self):
        # return chosen merging address
        merging_address = self.__SC.functions.get_merging_address().call()
        return merging_address
    
    def get_partial_model_rcd(self, addr):
        # return partial_model_rcd of specific node
        partial_model_rcd = self.__SC.functions.get_partial_model_rcd(addr).call()
        return partial_model_rcd
    
    def check_upload_status(self, addr):
        # return upload_status
        upload_status = self.__SC.functions.check_upload_status(addr).call()
        return upload_status
    
    def stack_ready_for_merge(self, hash_code, addr):
        # stack the recombined model hash code to smart contract
        trans = self.__SC.functions.stack_ready_for_merge(hash_code, addr).build_transaction(self.tx())
        self.sign_transaction(trans)

    def check_download_status(self, addr):
        # return download_status
        download_status = self.__SC.functions.check_download_status(addr).call()
        return download_status

    def get_ready_for_merge(self):
        # return waiting_for_merge
        ready_for_merge = self.__SC.functions.get_ready_for_merge().call()
        return ready_for_merge
    