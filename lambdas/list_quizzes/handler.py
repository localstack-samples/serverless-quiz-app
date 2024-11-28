import json
import boto3
from boto3.dynamodb.conditions import Attr

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Quizzes')

    try:
        response = table.scan(
            FilterExpression=Attr('Visibility').eq('Public'),
            ProjectionExpression='QuizID, Title, Visibility'
        )

        quizzes = response.get('Items', [])

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'Quizzes': quizzes})
        }

    except Exception as e:
        print(f"Error retrieving public quizzes: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'message': 'Error retrieving public quizzes', 'error': str(e)})
        }
