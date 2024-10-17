import json
import boto3
from decimal import Decimal, getcontext

def lambda_handler(event, context):
    getcontext().prec = 6

    dynamodb = boto3.resource('dynamodb')
    quizzes_table = dynamodb.Table('Quizzes')
    submissions_table = dynamodb.Table('UserSubmissions')
    stepfunctions = boto3.client('stepfunctions')

    for record in event['Records']:
        try:
            message_body = json.loads(record['body'])
            submission_id = message_body['SubmissionID']
            username = message_body['Username']
            quiz_id = message_body['QuizID']
            user_answers = message_body['Answers']
            email = message_body.get('Email')

            if not all([submission_id, username, quiz_id, user_answers]):
                print(f"Invalid message data: {message_body}")
                continue

            response = quizzes_table.get_item(Key={'QuizID': quiz_id})
            if 'Item' not in response:
                print(f"QuizID not found: {quiz_id}")
                continue

            quiz = response['Item']
            correct_answers = [q['CorrectAnswer'] for q in quiz['Questions']]
            total_questions = len(correct_answers)

            enable_timer = quiz.get('EnableTimer', False)
            timer_seconds = quiz.get('TimerSeconds', None)

            score = Decimal('0.0')
            for idx, correct in enumerate(correct_answers):
                question_idx = str(idx)
                if question_idx in user_answers:
                    user_answer_data = user_answers[question_idx]
                    user_answer = user_answer_data['Answer']
                    time_taken = Decimal(str(user_answer_data['TimeTaken']))
                    if str(user_answer) == str(correct):
                        if enable_timer and timer_seconds is not None:
                            timer_seconds_decimal = Decimal(str(timer_seconds))
                            if time_taken > timer_seconds_decimal:
                                question_score = Decimal('0.0')
                            else:
                                max_score = Decimal('100.0')
                                question_score = max_score * (Decimal('1.0') - (time_taken / timer_seconds_decimal))
                                if question_score < Decimal('0.0'):
                                    question_score = Decimal('0.0')
                        else:
                            question_score = Decimal('100.0')
                        score += question_score
                    else:
                        pass
                else:
                    pass

            submissions_table.put_item(Item={
                'SubmissionID': submission_id,
                'Username': username,
                'QuizID': quiz_id,
                'UserAnswers': user_answers,
                'Score': score,
                'TotalQuestions': Decimal(total_questions)
            })

            if email:
                state_machine_arn = 'arn:aws:states:us-east-1:000000000000:stateMachine:SendEmailStateMachine'
                input_data = {
                    'SubmissionID': submission_id,
                    'Username': username,
                    'Email': email,
                    'Score': float(score),
                    'TotalQuestions': total_questions
                }

                stepfunctions.start_execution(
                    stateMachineArn=state_machine_arn,
                    input=json.dumps(input_data, default=str)
                )

        except Exception as e:
            print(f"Error processing record {record}: {e}")
            continue
