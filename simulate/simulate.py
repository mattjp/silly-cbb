import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import json

DDB_TABLE_NAME = 'cbb_d1_teams_2021'
QSP = 'queryStringParameters'
TEAMS = 'teams'
ITEM = 'Item'
MIN_OFF_RBD = Decimal(3.97) # Static, pulled from DynamoDB
MAX_OFF_RBD = Decimal(13.5)
POWER_SIX = {
  'ACC':     1.05,
  'BIG12':   1.075,
  'BIGEAST': 1.05,
  'BIG10':   1.05,
  'PAC12':   1.05,
  'SEC':     1.025

}
GUARD_AGE_SCORE = {
  'FR': 0.0,
  'SO': 0.2,
  'JR': 0.7,
  'SR': 0.9,
  'GR': 1.0
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
  conf = stats['conference']
  ft_pct = round(stats['season_ft_pct'], 4)
  avg_guard_age = round(Decimal(sum(list(map(lambda g: GUARD_AGE_SCORE[g['experience']], stats['guards']))) / 2), 4)
  avg_off_rebound = round((round(stats['off_rebound_avg_pg'], 4) - MIN_OFF_RBD) / (MAX_OFF_RBD - MIN_OFF_RBD), 4) # Normalize
  conf_bonus = Decimal(POWER_SIX[conf]) if conf in POWER_SIX else Decimal(1)

  A = Decimal(0.8)
  B = Decimal(0.2)
  C = Decimal(0.01)

  score = ((A * ft_pct) + (B * avg_guard_age) + (C * avg_off_rebound)) * conf_bonus

  # score = (ft_pct + avg_guard_age + round((avg_off_rebound / 2), 4) ) * Decimal(conf_bonus)
  # (0.6*ft_pct + 0.3*avg_guard_age + 0.1*off_rbd) * conf_bonus

  return {
    'season_ft_pct': float(A * ft_pct), # str()
    'avg_guard_age': float(B * avg_guard_age),
    'avg_off_rebound': float(C * avg_off_rebound),
    'conf_bonus': float(conf_bonus),
    'score': float(score)
  }
