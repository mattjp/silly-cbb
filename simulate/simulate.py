import json

def lambda_handler(event, context):
  # TODO implement

  teams = event['queryStringParameters']['teams']

  return {
    'statusCode': 200,
    'body': json.dumps(teams)
  }