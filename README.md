# dbsec
## Usage:
	1. Set up your AWS account and create a S3 bucket
	2. Put your AWS access key ID and secret access key into `~/.aws/credentials`. File format looks like the credential file found [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)
	3. Setup your Ethereum accounts with [Metamask](https://metamask.io/download.html). You will need two accounts, one of which you will need the private key of. Put these into `~/.aws/eth_credentials`; the file format looks like this:
	`
	account1 = <account 1 ID>
	account2 = <account 2 ID>
	private_key = <account 1 private key>
	`
	4. Install the requirements: `pip install -r requirements.txt`
	5. Execute and follow the inline instructions: `python3.6 cloudsec.py`
## To test from scratch, use:
	`./test.sh`
