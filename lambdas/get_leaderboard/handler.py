import json
import boto3
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    try:
        quiz_id = event['queryStringParameters']['quiz_id']
        top = int(event['queryStringParameters'].get('top', 10))
    except (KeyError, TypeError, ValueError) as e:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'message': 'quiz_id is required and top should be an integer', 'error': str(e)})
        }

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('UserSubmissions')

    try:
        response = table.query(
            IndexName='QuizID-Score-index',
            KeyConditionExpression=Key('QuizID').eq(quiz_id),
            ScanIndexForward=False,
            Limit=top
        )
        items = response.get('Items', [])
        leaderboard = [
            {
                'Username': item['Username'],
                'Score': float(item['Score']),
                'SubmissionID': item['SubmissionID']
            } for item in items
        ]
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps(leaderboard)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'message': 'Error retrieving leaderboard', 'error': str(e)})
        }
