import json
import boto3
from decimal import Decimal

def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

def lambda_handler(event, context):
    try:
        quiz_id = event['queryStringParameters']['quiz_id']
    except (KeyError, TypeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'quiz_id is required', 'error': str(e)})
        }

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Quizzes')
    response = table.get_item(Key={'QuizID': quiz_id})

    if 'Item' in response:
        quiz = response['Item']
        for question in quiz['Questions']:
            question.pop('CorrectAnswer', None)
        quiz = convert_decimal(quiz)
        return {
            'statusCode': 200,
            'body': json.dumps(quiz)
        }
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'Quiz not found'})
        }
