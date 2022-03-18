import boto3
import requests
import json
import time

SPORT_RADAR_URL_PREFIX = 'https://api.sportradar.us/ncaamb/trial/v4/en'
S3_BUCKET = 'silly-cbb'
s3 = boto3.resource('s3')

def get_team_stats_url(team_id, api_key):
	return f'{SPORT_RADAR_URL_PREFIX}/seasons/2021/REG/teams/{team_id}/statistics.json?api_key={api_key}'


def get_player_stats_url(player_id, api_key):
	return f'{SPORT_RADAR_URL_PREFIX}/players/{player_id}/profile.json?api_key={api_key}'


def get_json_from_url(url):
	response = requests.get(url)
	return response.json()


def get_json_from_s3(s3_bucket, s3_key):
	content_obj = s3.Object(s3_bucket, s3_key)
	file_content = content_obj.get()['Body'].read().decode('utf-8')
	return json.loads(file_content)


def write_json_to_s3(json_content, s3_bucket, s3_key):
	content_obj = s3.Object(s3_bucket, s3_key)
	content_obj.put(Body=json.dumps(json_content))


def get_team_stats_and_write_to_s3(team_name, team_id, api_key):
	url = get_team_stats_url(team_id, api_key)
	json_content = get_json_from_url(url)
	write_json_to_s3(json_content, S3_BUCKET, f'teams/2021/{team_name}')


def get_guard_stats_and_write_to_s3(guard_id, api_key):
	url = get_player_stats_url(guard_id, api_key)
	json_content = get_json_from_url(url)
	write_json_to_s3(json_content, S3_BUCKET, f'players/2021/guards/{guard_id}')


def get_starting_guards(team_json):
	players = team_json['players']
	guards = list(filter(lambda player: player['position'] == 'G', players))
	return sorted(guards, key=lambda guard: guard['total']['games_started'], reverse=True)[:2]


def collect_team_stats(teams, api_key, sleep_time_seconds=2):
	for team in teams:
		team_name, team_id = team['school_name'], team['sport_radar_id']
		print(f'Collecting team stats for team: {team_name}...')
		get_team_stats_and_write_to_s3(team_name, team_id, api_key)
		time.sleep(sleep_time_seconds)


def collect_starting_guard_stats(teams, api_key, sleep_time_seconds=2):
	for team in teams:
		team_name = team['school_name']
		print(f'Collecting guard stats for team: {team_name}...')
		team_json = get_json_from_s3(S3_BUCKET, f'teams/2021/{team_name}')
		starting_guards = get_starting_guards(team_json)
		for guard in starting_guards:
			guard_id, guard_full_name = guard['id'], guard['full_name']
			print(f'Collecting stats for guard: {guard_full_name}')
			get_guard_stats_and_write_to_s3(guard_id, api_key)
			time.sleep(sleep_time_seconds)


def collect(teams, api_key, collect_team, collect_starting_guard):
	if collect_team:
		collect_team_stats(teams, api_key)
	if collect_starting_guard:
		collect_starting_guard_stats(teams, api_key)
