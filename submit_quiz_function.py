import json
import boto3
import uuid

def lambda_handler(event, context):
    try:
        submission = json.loads(event['body'])
        username = submission['Username']
        quiz_id = submission['QuizID']
        answers = submission['Answers']

        if not username or not quiz_id or not answers:
            raise ValueError("Username, QuizID, and Answers are required.")
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid input data', 'error': str(e)})
        }

    dynamodb = boto3.resource('dynamodb')
    quizzes_table = dynamodb.Table('Quizzes')

    try:
        response = quizzes_table.get_item(Key={'QuizID': quiz_id})
        if 'Item' not in response:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': f'QuizID "{quiz_id}" does not exist.'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error accessing the Quizzes table.', 'error': str(e)})
        }

    sqs = boto3.client('sqs')
    queue_url = sqs.get_queue_url(QueueName='QuizSubmissionQueue')['QueueUrl']

    message_body = {
        'SubmissionID': str(uuid.uuid4()),
        'Username': username,
        'QuizID': quiz_id,
        'Answers': answers
    }

    try:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error sending message to SQS.', 'error': str(e)})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Submission received', 'SubmissionID': message_body['SubmissionID']})
    }
