from web3 import Web3
import sys
import time
import math

#API from infura
infura_url = "https://ropsten.infura.io/v3/a51ee608e9e944edb0643b1b26a48eb1"

class Eth(object):
    def __init__(self, credential_path):
        #configure ethereum
        configureCount = 0
        with open(credential_path, "r") as f:
            for line in f:
                lineData = list(map(lambda x: x.strip(), line.split("=")))
                if lineData[0] == "account1":
                    self._acc1 = lineData[1]
                    configureCount += 1
                elif lineData[0] == "account2":
                    self._acc2 = lineData[1]
                    configureCount += 1
                elif lineData[0] == "private_key":
                    self._acc1Key = lineData[1]
                    configureCount += 1
        if configureCount != 3:
            print("Invalid Ethereum configuration")
            sys.exit(-1)
        self._w3 = Web3(Web3.HTTPProvider(infura_url))
        print("Connected to eth:", self._w3.isConnected())

    def upload(self, hashData):
        """
        Upload the hashData to the blockchain
        :param hashData: bytes object of hash to upload
        :return: transaction id of the upload
        """
        submData = hashData.hex()
        signed_txn = self._w3.eth.account.signTransaction(
            dict(
                nonce = self._w3.eth.getTransactionCount(self._acc1),
                gasPrice = self._w3.eth.gasPrice,
                gas = 100000,
                to = self._acc2,
                value = 1234567,
                data = submData,
            ),
            self._acc1Key,
        )
        txn_hash = self._w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        txn_hash_str = txn_hash.hex()
        self._w3.eth.waitForTransactionReceipt(txn_hash_str)
        print("transaction id:", txn_hash_str)
        return txn_hash_str


    def retrieve(self, block_id):
        pass
