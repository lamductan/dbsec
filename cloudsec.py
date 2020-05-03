import os
import sys
import time

from modules.user.user import User
from modules.eth.eth import Eth
from modules.backup_program.backup_program import BackupProgram


def main():
    HOME_DIRECTORY = os.path.expanduser("~")
    user = User(os.path.join(HOME_DIRECTORY, ".aws", "credentials"))
    eth = Eth(os.path.join(HOME_DIRECTORY, ".aws", "eth_credentials"))

    backupProgram = BackupProgram(user, eth)
    backupProgram.run()


if __name__ == '__main__':
    main()
