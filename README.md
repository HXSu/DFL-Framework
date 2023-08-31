Decentralized Federated Learning Based on Blockchain and IPFS  
===================================================================================================
  - [Preparation and requirements](#preparation-and-requirements)
    - [Clone project and set up the environment](#clone-project-and-set-up-the-environment)
    - [Install necessary softwares](#install-necessary-softwares)
    - [Turn on necessary services](#turn-on-necessary-services)
    - [Deploy smart contracts to the local blockchain](#deploy-smart-contracts-to-the-local-blockchain)
    - [Prepare your data](#prepare-your-data)
  - [Participate in the DFL as a single node](#participate-in-the-dfl-as-a-single-node)
  - [Deploy the DFL framework distributedly on local](#deploy-the-dfl-framework-distributedly-on-local)
    - [Modify the DFL framework deployment configuration](#modify-the-dfl-framework-deployment-configuration)
    - [Run the deployment script](#run-the-deployment-script)
---------------------------------------------------------------------------------------------------
## Preparation and requirements
### Clone project and set up the environment
1. Download the DFL_env.yml
2. Import the virtual environment and clone the project to a local directory

```bash
conda env create -f DFL_env.yml
conda activate DFL_env
git clone https://github.com/####
```
### Install necessary softwares
1. Install IPFS Kubo according to OS: [Download and install IPFS Kubo](https://docs.ipfs.tech/install/command-line/#install-official-binary-distributions)
2. After the installation is complete, check whether it is available
```bash
ipfs --version

> ipfs version 0.20.0
```
3. Install a local Ethereum blockchain, such as Ganache: [Download and install Ganache](https://www.trufflesuite.com/ganache)
### Turn on necessary services
1. Start IPFS daemon process and keep the process running in the background
```bash
ipfs init
ipfs daemon
```
2. Start Ganache and keep the process running in the background
### Deploy smart contracts to the local blockchain
The smart contract file is under the directory: `./smart_contract/DFL_contract.sol`
Specify the smart contract's constructor parameters according to the demand
- You can use Remix website to compile and deploy the smart contracts to the local blockchain: [Remix](https://remix.ethereum.org/)
- Or you can use Truffle to compile and deploy the smart contracts to the local blockchain: [Truffle](https://www.trufflesuite.com/docs/truffle/getting-started/installation)
---------------------------------------------------------------------------------------------------

### Prepare your data
1. Prepare your data and put it in the directory: `./all_data` under DFL_framework directory
2. The data is in the form of huggingface datasets. You can refer to the [huggingface datasets](https://huggingface.co/docs/datasets/) to prepare your data
3. There is a sample dataset in the directory: `./sample_data`, you can use it to test the DFL framework
## Participate in the DFL as a single node
1. Open the terminal and enter the `./DFL_framework` directory
2. Run the DFL framework and the interface is `front_end_menu.py`
```bash
cd ./DFL_framework
python front_end_menu.py
```
1. Interact with the DFL framework through the interface   

| MENU | DESCRIPTION |
| :--- | :--- |
| 1. Register | Register with wallet address and private key |
| 2. Train | Training the global model with local data |
| 3. Evaluate | Evaluating others' trained models |
| 4. Aggregation | Merge all approved models into a new global model |
| 5. Exit | Exit the system |

## Deploy the DFL framework distributedly on local
### Modify the DFL framework deployment configuration
1. Open the configuration file: `./deploy_nodes_config.json`  
2. Edit the parameters in the configuration file  
  `nodes_num:` Number of nodes will be deployed  
  `smart_contract_address:` Smart contract address deployed in the blockchain  
  `nodes_address:` List of nodes' wallet address. Length is equal to `nodes_num`. Can be obtained from Ganache  
  `nodes_private_key:` List of nodes' private key corresponding to the wallet address
### Run the deployment script
1. Open the terminal and enter the project directory
2. Run the deployment script. You can specify the deployment directory by modifying the args: `--deploy_dir`.  
The default deployment directory is `./deploy_nodes`  
```bash
python deploy_nodes.py
``` 
The number of nodes in `./deploy_nodes` is according to the `nodes_num` parameter in `./deploy_nodes_config.json`.  
The script will automatically distribute the dataset under `./sample_data` to each node according to the `nodes_num` parameter.  
Each directory contains its own DFL framework. The DFL framework of each node is independent and can be deployed on different machines.   
Treat each node's directory as a single node and follow the steps in [Participate in the DFL as a single node](#participate-in-the-dfl-as-a-single-node) to interact with the DFL framework.

