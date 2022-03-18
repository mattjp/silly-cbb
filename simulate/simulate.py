import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import json

DDB_TABLE_NAME = 'cbb_d1_teams_2021'
QSP = 'queryStringParameters'
TEAMS = 'teams'
ITEM = 'Item'
POWER_SIX = {
  'ACC':     1.05,
  'BIG12':   1.075,
  'BIGEAST': 1.05,
  'BIG10':   1.05,
  'PAC12':   1.05,
  'SEC':     1.025

}
GUARD_AGE_SCORE = {
  'FR': 1.0,
  'SO': 1.0,
  'JR': 1.025,
  'SR': 1.05,
  'GR': 1.05
}

# Static, pulled from DynamoDB
MIN_OFF_RBD = Decimal(3.97) 
MAX_OFF_RBD = Decimal(13.5)
MIN_FT_PCT  = Decimal(0.6)
MAX_FT_PCT  = Decimal(0.825)
MIN_FT_ATT  = Decimal(11.78)
MAX_FT_ATT  = Decimal(23.43)

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
  ft_pct = stats['season_ft_pct']
  off_rbd_avg = stats['off_rebound_avg_pg']

  # Normalized statistics, range 0-1
  norm_ft_pct = (ft_pct - MIN_FT_PCT) / (MAX_FT_PCT - MIN_FT_PCT)
  norm_avg_off_rbd = (off_rbd_avg - MIN_OFF_RBD) / (MAX_OFF_RBD - MIN_OFF_RBD)
  
  # Bonus multipliers, between 0-5%
  avg_guard_age = Decimal(sum(list(map(lambda g: GUARD_AGE_SCORE[g['experience']], stats['guards']))) / 2)
  conf_bonus = Decimal(POWER_SIX[conf]) if conf in POWER_SIX else Decimal(1)

  # A = Decimal(0.8)
  # B = Decimal(0.2)
  # C = Decimal(0.01)

  A = Decimal(0.8)
  B = Decimal(0.2)

  score = (((A * norm_ft_pct) + (B * norm_avg_off_rbd)) * avg_guard_age) * conf_bonus
  # score = ((A * ft_pct) + (B * avg_guard_age) + (C * avg_off_rebound)) * conf_bonus # V2
  # score = (ft_pct + avg_guard_age + round((avg_off_rebound / 2), 4) ) * Decimal(conf_bonus) # V1

  return {
    'season_ft_pct': float(norm_ft_pct),
    'avg_guard_age': float(avg_guard_age),
    'avg_off_rebound': float(norm_avg_off_rbd),
    'conf_bonus': float(conf_bonus),
    'score': float(score)
  }
