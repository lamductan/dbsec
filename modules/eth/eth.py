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
        self._transactionCount = self._w3.eth.getTransactionCount(self._acc1)

    def upload(self, hashData):
        """
        Upload the hashData to the blockchain
        :param hashData: hex string of hash to upload
        :return: transaction id of the upload
        """
        while True:
            try:
                myNonce = max(self._transactionCount, self._w3.eth.getTransactionCount(self._acc1))
                signed_txn = self._w3.eth.account.signTransaction(
                    dict(
                        nonce = myNonce,
                        gasPrice = self._w3.eth.gasPrice,
                        gas = 100000,
                        to = self._acc2,
                        value = 1234567,
                        data = hashData,
                    ),
                    self._acc1Key,
                )
                txn_hash = self._w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                txn_hash_str = txn_hash.hex()
                self._transactionCount = myNonce + 1
                break
            except:
                print("eth error, raising nonce")
                self._transactionCount += 1
        while True:
            try:
                self._w3.eth.waitForTransactionReceipt(txn_hash_str)
                break
            except:
                print("eth timed out, trying again")
        print("transaction id:", txn_hash_str)
        return txn_hash_str


    def retrieve(self, block_id):
        """
        Retrieve the stored data from the blockchain
        :param block_id: transaction id
        :return: what was stored at the blockchain as input (the hash)
        """
        transaction = self._w3.eth.getTransaction(block_id)
        storedHash = transaction["input"]   #this is a string with 0x as the prefix
        #TODO: compare this with the computed hash of a retrieved version
        print("stored hash:", storedHash)
        return storedHash
