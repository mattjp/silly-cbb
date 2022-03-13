import boto3
from decimal import Decimal
import requests
import json
import time

"""
1. get all teams from table (1 query)
2. for each team, call the season stats API
2.5. put the new data in s3?
3. update team in DDB
"""

DDB_TABLE_NAME = 'cbb_d1_teams_2021'

def get_all_teams():
	dyanmodb = boto3.resource('dynamodb', region_name='us-east-2')
	table = dyanmodb.Table(DDB_TABLE_NAME)

	response = table.scan()
	return response.get('Items', [])


def add_team_stats_to_s3(teams): # this is uploading to s3
	updated_teams = []
	for team in teams:
		get_team_stats(team)
		time.sleep(2) # API rate limit is 1 req/sec


def get_team_stats(team):
	print(f"Getting stats for {team['school_name']}...")

	url = f"https://api.sportradar.us/ncaamb/trial/v4/en/seasons/2021/REG/teams/{team['sport_radar_id']}/statistics.json?api_key="
	response = requests.get(url)
	json_content = response.json()

	s3 = boto3.resource('s3')
	content_obj = s3.Object('silly-cbb', f"teams/{team['school_name']}")
	content_obj.put(Body=json.dumps(json_content))


def get_team_stats_from_s3(team_name):
	# all of this is duplicate
	s3 = boto3.resource('s3')
	content_obj = s3.Object('silly-cbb', f"teams/{team_name}")
	file_content = content_obj.get()['Body'].read().decode('utf-8')
	json_content = json.loads(file_content)
	return json_content


def get_starting_guards(team_stats_json):
	# starting = highest avg minutes played for the season
	players = team_stats_json['players']
	guards = list(filter(lambda player: player['position'] == 'G', players))
	# print(guards)

	return sorted(guards, key=lambda guard: guard['total']['games_started'], reverse=True)[:2]


def create_guard_obj(guard):
	s3 = boto3.resource('s3') # sneak s3 call in here, then call in lambda
	content_obj = s3.Object('silly-cbb', f"players/2021/guards/{guard['id']}")
	file_content = content_obj.get()['Body'].read().decode('utf-8')
	json_content = json.loads(file_content)
	exp = json_content['experience']

	return {
		'full_name': guard['full_name'],
		'sport_radar_id': guard['id'],
		'experience': exp
	}

def add_guard_data_to_table(guards, team):
	dyanmodb = boto3.resource('dynamodb', region_name='us-east-2')
	table = dyanmodb.Table(DDB_TABLE_NAME)

	table.update_item(
		Key={
			'school_name': team['school_name']
		},
		UpdateExpression='set guards = :g',
		ExpressionAttributeValues={
			':g': list(map(create_guard_obj, guards))
		},
		ReturnValues='UPDATED_NEW'
	)


def add_all_guard_data_to_s3(teams):
	for team in teams:
		print(f"Getting guard stats for {team['school_name']}...")

		guards = team['guards']
		for guard in guards:
			print(guard['full_name'])
			url = f"https://api.sportradar.us/ncaamb/trial/v4/en/players/{guard['sport_radar_id']}/profile.json?api_key="
			response = requests.get(url)
			json_content = response.json()

			s3 = boto3.resource('s3')
			content_obj = s3.Object('silly-cbb', f"players/2021/guards/{guard['sport_radar_id']}")
			content_obj.put(Body=json.dumps(json_content))
			time.sleep(2) # API rate limit is 1 req/sec


def add_team_stats_to_table(team_stats_json):
	dyanmodb = boto3.resource('dynamodb', region_name='us-east-2')
	table = dyanmodb.Table(DDB_TABLE_NAME)

	total_stats = team_stats_json['own_record']['total']
	avg_stats = team_stats_json['own_record']['average']

	tot_ft_pct = total_stats['free_throws_pct']
	off_rbd_avg = avg_stats['off_rebounds']
	ft_att_avg = avg_stats['free_throws_att']

	print(tot_ft_pct, off_rbd_avg, ft_att_avg)

	table.update_item(
		Key={
			'school_name': team['school_name']
		},
		UpdateExpression='set season_ft_pct = :ftp, off_rebound_avg_pg = :ora, ft_att_avg_pg = :faa',
		ExpressionAttributeValues={
			':ftp': Decimal(str(tot_ft_pct)),
			':ora': Decimal(str(off_rbd_avg)),
			':faa': Decimal(str(ft_att_avg))
		},
		ReturnValues='UPDATED_NEW'
	)


if __name__ == '__main__':
	all_teams = get_all_teams()
	# add_team_stats_to_s3(all_teams)
	for team in all_teams:
		print(team['school_name'])
		team_stats_json = get_team_stats_from_s3(team['school_name'])
		add_team_stats_to_table(team_stats_json)
		# starting_guards = get_starting_guards(tsj)
		# add_guard_data_to_table(starting_guards, team)
		# break
	# add_all_guard_data_to_s3(all_teams)
	# add_guard_exp_to_table(all_teams)




