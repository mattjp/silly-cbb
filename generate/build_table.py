import boto3
import json
import re

DDB_TABLE_NAME = 'cbb_d1_teams_2021'
S3_BUCKET = 'silly-cbb' 
S3_KEY = 'standings_2021.json' # these 3 things should all be CLI args - pass in DDB table name + S3 URI
# Create the table programmatically if it doesn't exist?


D1_CONFERENCES = set([
	'AE',
	'AAC',
	'AS',
	'A10',
	'ACC',
	'BIG12',
	'BIGEAST',
	'BIGSKY',
	'BIGSOUTH',
	'BIG10',
	'BIGWEST',
	'COLONIAL',
	'CUSA',
	'HORIZON',
	'IVY',
	'MAAC',
	'MAC',
	'MEAC',
	'MVC',
	'MWC',
	'NE',
	'OVC',
	'PAC12',
	'PATRIOT',
	'SEC',
	'SOUTHERN',
	'SOUTHLAND',
	'SWAC',
	'SUMMIT',
	'SUNBELT',
	'WCC',
	'WAC'
])

def get_standings():
	s3 = boto3.resource('s3')
	content_obj = s3.Object(S3_BUCKET, S3_KEY)
	file_content = content_obj.get()['Body'].read().decode('utf-8')
	json_content = json.loads(file_content)
	return json_content


def get_all_conferences(standings):
	return standings['conferences']


def filter_d1_conferences(all_conferences):
	return list(filter(lambda conference: conference['alias'] in D1_CONFERENCES, all_conferences))


def normalize_str(s):
	s_alnum = re.sub(r'[^A-Za-z0-9- ]+', '', s)
	return s_alnum.lower().replace(' ', '-')


def write_teams(d1_conferences):
	dyanmodb = boto3.resource('dynamodb', region_name='us-east-2')
	table = dyanmodb.Table(DDB_TABLE_NAME)

	for conference in d1_conferences:
		print('Writing ' + conference['alias'] + ' to DyanmoDB...')

		for team in conference['teams']:
			table.put_item(
				Item = {
					'school_name': normalize_str(team['market']),
					'sport_radar_id': team['id'],
					'mascot': normalize_str(team['name']),
					'conference': conference['alias']
				}
			)


if __name__ == '__main__':
	standings = get_standings()
	all_conferences = get_all_conferences(standings)
	d1_conferences = filter_d1_conferences(all_conferences)
	write_teams(d1_conferences)
	



