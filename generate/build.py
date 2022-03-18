import boto3
from generate.collect import get_json_from_s3, get_starting_guards
from decimal import Decimal
import json
import re

s3 = boto3.resource('s3')
dyanmodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dyanmodb.Table('cbb_d1_teams_2021')
S3_BUCKET = 'silly-cbb'
D1_CONFERENCES = set([
	'AE', 'AAC', 'AS', 'A10', 'ACC', 'BIG12', 'BIGEAST', 'BIGSKY', 'BIGSOUTH', 'BIG10', 'BIGWEST', 'COLONIAL', 'CUSA',
	'HORIZON', 'IVY', 'MAAC', 'MAC', 'MEAC', 'MVC', 'MWC', 'NE', 'OVC', 'PAC12', 'PATRIOT', 'SEC', 'SOUTHERN', 
	'SOUTHLAND', 'SWAC', 'SUMMIT', 'SUNBELT', 'WCC', 'WAC'
])


def get_team_standings_json(s3_bucket, s3_key):
	return get_json_from_s3(s3_bucket, s3_key)


def get_conference_json(team_standings_json):
	return team_standings_json['conferences']


def get_d1_conferences(conference_json):
	return list(filter(lambda conference: conference['alias'] in D1_CONFERENCES, conference_json))


def normalize_str(s):
	s_alnum = re.sub(r'[^A-Za-z0-9- ]+', '', s)
	return s_alnum.lower().replace(' ', '-')


def get_all_teams_from_table():
	response = table.scan()
	return response.get('Items', [])


def write_conferences_to_table(conferences):
	for conference in conferences:
		conference_name = conference['alias']
		print(f'Writing teams for conference: {conference_name}')
		for team in conference['teams']:
			table.put_item(
				Item = {
					'school_name': normalize_str(team['market']),
					'sport_radar_id': team['id'],
					'mascot': normalize_str(team['name']),
					'conference': conference_name
				}
			)


def write_team_stats_json_to_table(team_json):
	total_stats = team_json['own_record']['total']
	avg_stats = team_json['own_record']['average']

	tot_ft_pct = total_stats['free_throws_pct']
	off_rbd_avg = avg_stats['off_rebounds']
	ft_att_avg = avg_stats['free_throws_att']

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


def create_guard_obj(guard):
	guard_id = guard['id']
	guard_json = get_json_from_s3(S3_BUCKET, f'players/2021/guards/{guard_id}')
	exp = guard_json['experience']

	return {
		'full_name': guard['full_name'],
		'sport_radar_id': guard_id,
		'experience': exp
	}


def write_guards_stats_json_to_table(guards_json, team_name):
	table.update_item(
		Key={
			'school_name': team_name
		},
		UpdateExpression='set guards = :g',
		ExpressionAttributeValues={
			':g': list(map(create_guard_obj, guards))
		},
		ReturnValues='UPDATED_NEW'
	)


def initialize_table(s3_bucket, s3_key):
	team_standings_json = get_team_standings_json(s3_bucket, s3_key)
	conference_json = get_conference_json(team_standings_json)
	d1_conferences = get_d1_conferences(conference_json)
	write_conferences_to_ddb(d1_conferences)


def write_team_stats_to_table(teams):
	for team in teams:
		team_name = team['school_name']
		print(f'Writing team stats for team: {team_name}')
		team_json = get_json_from_s3(S3_BUCKET, f'teams/2021/{team_name}')
		write_team_stats_json_to_table(team_json)


def write_guard_stats_to_table(teams):
	for team in teams:
		team_name = team['school_name']
		print(f'Writing guard stats for team: {team_name}')
		team_json = get_json_from_s3(S3_BUCKET, f'teams/2021/{team_name}')
		guards_json = get_starting_guards(team_json)
		write_guards_stats_json_to_table(guards_json, team_name)


def build(s3_bucket, s3_key, teams):
	if initalize:
		initalize_table(s3_bucket, s3_key)
	if write_teams:
		write_team_stats_to_table(teams)
	if write_guards:
		write_guard_stats_to_table(teams)
