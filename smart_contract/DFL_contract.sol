//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DFL_CONTRACT {

    uint epoch_num; // record the current epoch
    uint16 stage; // record the current stage, 0:train; 1:evaluation; 2:upload partial 3:download partial&recombination 4:merge

    struct pending_model{ // model that is waiting for evaluation
        string model_hash_code;
        uint64 evaluation_score;
        uint64 num_evaluators;
        uint16 approve_status; // 0:unapproved; 1:approved; 2:undecided

        address payable model_owner;
    }

    struct nodes{ // node register record
        address deposit_address;
        bool online;
    }

    struct approved_node{ // approved node record
        address node_address;
        bool partial_flag;
        bool recomb_flag;
        string [] partial_rcd;
    }

    uint num_nodes; // number of nodes limit
    nodes [] all_nodes; // all registered nodes record

    string global_model; // global model hash code
    pending_model[] pending_models; // pending model record
    approved_node [] approved_nodes; // nodes that has been approved to merge
    address [] unapproved_nodes; // nodes that has been unapproved to merge
    string [] ready_for_merge; // recombined model that is waiting for merging

    uint64 evaluation_threshold; // threshold of evaluation score
    uint merging_index; // index of the node that is going to merge

    constructor() payable{
        epoch_num = 0;
        stage = 0;
        global_model = "QmY75bMVvFW7bb1kGvnhvAnZz7FQ1QUrksABz5bKtLCSWj";
        evaluation_threshold = 10;
        num_nodes = 3;
    }

    receive() external payable {} // Function to receive Ether. msg.data must be empty

    fallback() external payable {} // Fallback function is called when msg.data is not empty

    function get_deposit_address_arr() public view returns (address [] memory) {
        // return the array of deposit addresses
        address [] memory deposit_address = new address [] (all_nodes.length);
        for (uint i=0; i<all_nodes.length; i++){
            deposit_address[i] = all_nodes[i].deposit_address;
        }
        return deposit_address;
    }

    function get_pending_model_info(uint index) public view returns (string memory, uint, uint, uint16, address){
        // return pending model info according to the index
        require(index < pending_models.length, "index out of range");

        return (pending_models[index].model_hash_code, 
                pending_models[index].evaluation_score, 
                pending_models[index].num_evaluators,
                pending_models[index].approve_status,
                pending_models[index].model_owner);
    }
    
    function get_global_model_info() public view returns (string memory){
        // return the hash code of the global model
        require(bytes(global_model).length > 0, "global model is empty");
        return global_model;
    }

    function get_pending_model_length() public view returns (uint){
        // return the length of pending model array
        return pending_models.length;
    }

    function get_pending_model_status(uint index) public view returns (uint16){
        // return the approve status of the pending model according to the index
        require(index < pending_models.length, "index out of range");
        return pending_models[index].approve_status;
    }

    function get_merging_address() public view returns (address){
        // return the address of the node that is going to merge
        require(merging_index < all_nodes.length, "index out of range");
        return all_nodes[merging_index].deposit_address;
    }

    function get_index_of_model(address addr) private view returns (uint){
        // return the index of the node according to the deposit address
        for (uint i=0; i<pending_models.length; i++){
            if (pending_models[i].model_owner == addr){
                return i;
            }
        }
        return 0;
    }

    function rand_num(uint upper) private view returns (uint){
        // generate random number
        return uint(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, msg.sender))) % upper;
    }

    function get_stage() public view returns (uint16){
        // return the current stage
        return stage;
    }

    function get_approved_nodes() public view returns (address [] memory){
        // return the array of approved nodes
        address [] memory app_nodes = new address [] (approved_nodes.length);
        for (uint i=0; i<approved_nodes.length; i++){
            app_nodes[i] = approved_nodes[i].node_address;
        }
        return app_nodes;
    }

    function get_approved_nodes_length() public view returns (uint){
        // return the length of approved nodes array
        return approved_nodes.length;
    }

    function get_partial_model_rcd(address addr) public view returns (string [] memory){
        // get specific node's partial model record
        for (uint i=0; i<approved_nodes.length; i++){
            if (approved_nodes[i].node_address == addr){
                return approved_nodes[i].partial_rcd;
            }
        }
        return new string [] (0);
    }

        function check_upload_status(address addr) public view returns (bool){
        // check if msg.sender has uploaded its partial model
        for (uint i=0; i<approved_nodes.length; i++){
            if (approved_nodes[i].node_address == addr){
                return approved_nodes[i].partial_flag;
            }
        }
        return false;
    }

    function check_download_status(address addr) public view returns (bool){
        // check if msg.sender has downloaded its partial model
        for (uint i=0; i<approved_nodes.length; i++){
            if (approved_nodes[i].node_address == addr){
                return approved_nodes[i].recomb_flag;
            }
        }
        return false;
    }

    function check_partial_finished() private view returns (bool){
        // if all nodes have uploaded their partial models, return true
        for (uint i=0; i<approved_nodes.length; i++){
            if (approved_nodes[i].partial_rcd.length  < (approved_nodes.length - 1)){
                return false;
            }
        }
        return true;
    }

    function get_ready_for_merge() public view returns (string [] memory){
        // return the array of recombined models
        return ready_for_merge;
    }

// ===================================================================================================

    function stack_node(address addr) public{
        // record the node that has registered
        all_nodes.push(nodes(addr, true));
    }

    function get_reward() public{
        // reward the node for its contribution
        require(address(this).balance>=0.1 ether,"not enough money");
        address payable _payableAddr = payable(msg.sender);
        _payableAddr.transfer(0.1 ether);
    }

    function update_online(address addr, bool online) public{
        // node update its online status
        for (uint i=0; i<all_nodes.length; i++){
            if (all_nodes[i].deposit_address == addr){
                all_nodes[i].online = online;
            }
        }
    }

    function stack_pending_model(string memory hash_code, address model_owner) public{
        // stack trained model to pending model array
        pending_model memory new_model = pending_model(hash_code, 0, 0, 2, payable(model_owner));
        pending_models.push(new_model);
        if (pending_models.length == num_nodes){
            stage = 1; // go to evaluation stage
        }
    }

    function random_merging_index() public{
        // randomly choose a online node to merge
        uint rand = rand_num(all_nodes.length);
        for (uint i=0; i<100; i++){ // try 100 times to randomly choose a online node
            rand = rand_num(all_nodes.length);
            if (all_nodes[rand].online == true){
                break;
            }
        }
        merging_index = rand;
    }

    function update_pending_model_evaluation_score(uint index, uint64 score_plus) public{
        // update the evaluation score of the model according to the evaluation result
        // if the evaluation score is greater than the threshold, change approve status
        // if the evaluation score is less than the threshold and all nodes have evaluated the model, stack the model to unapproved model array
        require(index < pending_models.length, "index out of range");
        pending_models[index].evaluation_score += score_plus;
        pending_models[index].num_evaluators += 1;

        if (pending_models[index].evaluation_score >= evaluation_threshold){
            pending_models[index].approve_status = 1;
            approved_node memory new_node = approved_node(pending_models[index].model_owner, false, false, new string [] (0));
            approved_nodes.push(new_node);
        }
        else if (pending_models[index].num_evaluators >= (num_nodes-1)){ // if all nodes have evaluated the model, but the evaluation score is less than the threshold, reject the model
            pending_models[index].approve_status = 0;
            unapproved_nodes.push(pending_models[index].model_owner);
        }

        if ((approved_nodes.length + unapproved_nodes.length) >= num_nodes){
            stage = 2; // go to upload partial stage
        }
    }

    function upload_partial_model(string [] memory partial_models) public{
        // upload partial model to the contract
        uint j = 0;
        for (uint i=0; i<approved_nodes.length; i++){
            if (approved_nodes[i].node_address == msg.sender){
                approved_nodes[i].partial_flag = true;
            }else{
                approved_nodes[i].partial_rcd.push(partial_models[j]);
                j++;
            }
        }
        if (check_partial_finished()){
            stage = 3; // go to download partial and upload recombination stage
        }
    }

    function update_global_model(string memory hash_code) public{
        // update global model hash code
        global_model = hash_code;
    }

    function stack_ready_for_merge(string memory hash_code, address addr) public{
        // stack recombined model to waiting for merge array
        ready_for_merge.push(hash_code);

        for (uint i=0; i<approved_nodes.length; i++){
            if (approved_nodes[i].node_address == addr){
                approved_nodes[i].recomb_flag = true;
            }
        }

        if (ready_for_merge.length == approved_nodes.length){
            stage = 4; // go to merge stage
            random_merging_index();
        }
    }

    function epoch_iteration() public{
        // reset and go next epoch
        delete all_nodes;
        delete approved_nodes;
        delete unapproved_nodes;
        delete ready_for_merge;
        delete pending_models;

        stage = 0;
        merging_index = 0;

        return_deposit();
        epoch_num += 1;
    }

    function return_deposit() public{
        // return deposit to those good-performance nodes
        // reward and punish according to the approved model number
        uint rt = 0;
        if (approved_nodes.length > 0){
            rt = (1 ether * all_nodes.length) / approved_nodes.length;
        }
        
        for (uint i=0; i<approved_nodes.length; i++){
            address payable _payableAddr = payable(approved_nodes[i].node_address);
            _payableAddr.transfer(rt);
        }
    }
}
