import argparse
import generate.collect
import generate.build

def generate_handler():
	print('Running generate handler...')

	parser = argparse.ArgumentParser()

	# parser.add_argument("-db", "--hostname", help="Database name")
	# get-team-data
	# get-guard-data
	# ddb-table-name
	# api-key
	# s3 bucket?
	# s3 standings key?



"""
required: ddb table name, S3 bucket? 

1. should we initialize? yes - then we need standings bucket
2. should we collect team stats? yes - then we need api key
3. should we collect guard stats?
4. should we write team stats to table?
5. should we write guard stats to table?
"""

	







if __name__ == '__main__':
	generate_handler()
