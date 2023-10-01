import os
import gnupg

class GPGEncryptor:
    def __init__(self, gpg_home):
        self.gpg = gnupg.GPG(gpg_home)

    def generate_key(self, name_real, name_email, passphrase='passphrase', expire_date='356d'):
        private_keys = self.gpg.list_keys(True)
        for ele in private_keys:
            if (ele["uids"][0].split(" ")[0]) == name_real:
                print("You already have a private key")
                return ele["fingerprint"]

        input_data = self.gpg.gen_key_input(
            name_real=name_real,
            name_email=name_email,
            passphrase=passphrase,
            expire_date=expire_date
        )
        key = self.gpg.gen_key(input_data)
        return key.fingerprint
        
    def import_public_key(self, public_key_path):
        import_result = self.gpg.import_keys_file(public_key_path)
        return import_result
        
    def export_my_public_key(self, fingerprint, output_path):
        self.gpg.export_keys(fingerprint, output=output_path)
        return output_path
        
    def encrypt_message(self, message, fingerprint):
        encrypted = self.gpg.encrypt(message, fingerprint)
        return encrypted
    
    def decrypt_message(self, encrypted_message, passphrase='passphrase'):
        decrypted = self.gpg.decrypt(encrypted_message, passphrase=passphrase)
        return decrypted