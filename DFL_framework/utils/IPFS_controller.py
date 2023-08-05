# please install the go-ipfs and run it first(https://docs.ipfs.tech/install/command-line/)
# otherwise, we are offline of the IPFS server and cannot upload or download files


import json
import requests
import os


class IPFSApiClient:
    def __init__(self, host="http://127.0.0.1:5001"):
        self.__host = host
        self.__upload_url = self.__host + "/api/v0/add"
        self.__cat_url = self.__host + "/api/v0/cat"
        self.__version_url = self.__host + "/api/v0/version"
        self.test_connection()
 
    def test_connection(self):
        """
        Test if the request can be connected
        :return:
        """
        try:
            requests.post(self.__version_url, timeout=10)
            # print("IPFS service is enabled")
        except requests.exceptions.ConnectTimeout:
            raise SystemExit("Connection timeout, please ensure that IPFS service is enabled")
        except requests.exceptions.ConnectionError:
            raise SystemExit("Unable to connect to %s " % self.__host)
 
    def upload_file(self, file_path):
        """
        :param file_path: Upload file path
        :return: File hash code
        """
        try:
            file = open(file_path, mode='rb')
        except FileNotFoundError:
            raise FileExistsError("The file does not exist!")
 
        files = {
            'file': file
        }
        response = requests.post(self.__upload_url, files=files)
        if response.status_code == 200:
            data = json.loads(response.text)
            hash_code = data['Hash']
        else:
            hash_code = None
 
        return hash_code
 
    def cat_hash(self, hash_code):
        """
        Read file contents
        :param hash_code:
        :return:
        """
        params = {
            'arg': hash_code
        }
        response = requests.post(self.__cat_url, params=params)
        if response.status_code == 200:
            return response.text.decode("utf-8")
        else:
            return "No data acquired!"
 
    def download_hash(self, hash_code, save_path):
        """
        Read file contents
        :param hash_code:
        :param save_path:  File save path
        :return:
        """
        if not os.path.exists("./model_storage"):
            os.makedirs("./model_storage")

        params = {
            'arg': hash_code
        }
        response = requests.post(self.__cat_url, params=params)
        if response.status_code == 200:
            with open(save_path, mode='wb') as f:
                f.write(response.content)
            return True, 'Save successfully'
        else:
            return False, "No data acquired!"
