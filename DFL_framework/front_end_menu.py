"""
This is the menu for DFL system.
Users can interact with the system through this menu.
Stage shows what's going on in the system.
"""
import os
from func_timeout import func_timeout, FunctionTimedOut
from transfer_manager import TransferManager

tm = TransferManager()
stage_dict = {
            "0": "train",
            "1": "evaluate",
            "2": "upload partial",
            "3": "download partial&recombination",
            "4": "merge"
            }
def print_menu():
    print()
    print("MENU<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    print("Welcome to Decentralized Federated Learning(DFL) system!")
    print(f"Current stage: {tm.stage}: {stage_dict[str(tm.stage)]}")
    print("Please choose the following options:")
    print("1. Register: Register with wallet address and private key")
    print("2. Train: Training the global model with local data")
    print("3. Evaluate: Evaluating others' trained models")
    print("4. Aggregation: Merge all approved models into a new global model")
    print("5. Exit: Exit the system")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    try:
        choice = func_timeout(600, lambda: input("Please input your choice (1/2/3/4/5): "))
        print()
        return choice
    except FunctionTimedOut:
        print("Time out!")
        return '5'

def main():
    tm.update_online(tm.config["my_address"], True)
    while 1:
        choice = print_menu()

        if choice == '1':
            os.system("python register.py")
        elif choice == '2':
            os.system("python training_scheduler.py")    
        elif choice == '3':
            os.system("python evaluating_scheduler.py")
        elif choice == '4':
            os.system("python aggregation_scheduler.py")
        elif choice == '5':
            break
        else:
            print("Invalid input! Please input again (1/2/3/4/5):")
    tm.sign_out(tm.config["my_address"])
    print("Thank you for using DFL system!")

if __name__=="__main__":
    main()
    exit(0)
