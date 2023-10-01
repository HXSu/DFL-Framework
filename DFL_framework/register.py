"""
This is a register script that participants can use to register to the system.
To guarantee the fairness of the system, each participant needs to pay some ether as refundable deposit.
"""
from transfer_manager import TransferManager
tm = TransferManager()
def main():
    print("Checking if you are registered...")
    my_address = tm.config["my_address"]
    deposit_address_arr = tm.smart_contract_handler.get_deposit_address()
    if my_address in deposit_address_arr:
        print("Already registered!")
    else:
        print("You are not registered yet! You can register now which requires 1 ether refundable deposit.")
        choice = input("Do you want to register? (y/n): ")
        while (choice.lower() != 'y') and (choice.lower() != 'n'):
            choice = input("Invalid input! Please input again! Do you want to register? (y/n): ")
        if choice == 'y':
            print("Registering...")
            if len(tm.config["my_address"]) <= 0:
                my_addr = input("Please input your ethereum address for registration: ")
                tm.config["my_address"] = my_addr
                my_key = input("Please input your ethereum private key for registration: ")
                tm.config["my_key"] = my_key
            tm.regist()
            print("Registered!")
        else:
            print("Register is required. You can do it later. Bye!")
            exit(0)

if __name__ == "__main__":
    main()
    exit(0)
