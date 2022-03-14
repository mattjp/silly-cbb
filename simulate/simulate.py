import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import json

DDB_TABLE_NAME = 'cbb_d1_teams_2021'
QSP = 'queryStringParameters'
TEAMS = 'teams'
ITEM = 'Item'
GUARD_AGE_SCORE = {
  'FR': 0.1,
  'SO': 0.2,
  'JR': 0.3,
  'SR': 0.4,
  'GR': 0.5
}

def lambda_handler(event, context):

  if not validate_input(event):
    return {
      'statusCode': 400,
      'body': json.dumps('Input not properly formatted.')
    }

  teams = event[QSP][TEAMS].split(',', 1)
  ddb_teams = {}
  dyanmodb = boto3.resource('dynamodb', region_name='us-east-2')
  table = dyanmodb.Table(DDB_TABLE_NAME)
  for team in teams:
    try:
      resp = table.get_item(Key={'school_name': team})
      if ITEM not in resp:
        raise ClientError({}, '') # could put error message here
      ddb_teams[team] = resp['Item']
    except ClientError as e:
      return {
        'statusCode': 400,
        'body': json.dumps(f'Team \'{team}\' not found in database.') # e.response['Error']['Message']
      }

  scores = {}
  for name, stats in ddb_teams.items():
    scores[name] = score(stats)

  return {
    'statusCode': 200,
    'body': json.dumps(scores)
  }


def validate_input(event):
  if QSP not in event:
    return False

  params = event[QSP]
  if TEAMS not in params:
    return False

  query_teams = params[TEAMS]
  teams = query_teams.split(',')
  if len(teams) != 2:
    return False

  return True


def score(stats):
  ft_pct = round(stats['season_ft_pct'], 2)
  avg_guard_age = round(Decimal(sum(list(map(lambda g: GUARD_AGE_SCORE[g['experience']], stats['guards']))) / 2), 2)
  avg_off_rebound = round(stats['off_rebound_avg_pg'], 2)

  score = ft_pct + avg_guard_age + round((avg_off_rebound / 100), 2)

  return {
    'season_ft_pct': float(ft_pct), # str()
    'avg_guard_age': float(avg_guard_age),
    'avg_off_rebound': float(avg_off_rebound),
    'score': float(score)
  }
