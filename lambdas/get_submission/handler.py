import json
import boto3
from decimal import Decimal

def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        # Convert Decimal to int or float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

def lambda_handler(event, context):
    try:
        submission_id = event['queryStringParameters']['submission_id']
    except (KeyError, TypeError) as e:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'message': 'submission_id is required', 'error': str(e)})
        }

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('UserSubmissions')
    response = table.get_item(Key={'SubmissionID': submission_id})

    if 'Item' in response:
        submission = response['Item']
        # Convert Decimal objects to int or float
        submission = convert_decimal(submission)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps(submission)
        }
    else:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'message': 'Submission not found'})
        }
