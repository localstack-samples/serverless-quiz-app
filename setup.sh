#!/bin/bash

awslocal dynamodb create-table \
    --table-name Quizzes \
    --attribute-definitions AttributeName=QuizID,AttributeType=S \
    --key-schema AttributeName=QuizID,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

awslocal dynamodb create-table \
    --table-name UserSubmissions \
    --attribute-definitions \
        AttributeName=SubmissionID,AttributeType=S \
        AttributeName=QuizID,AttributeType=S \
        AttributeName=Score,AttributeType=N \
    --key-schema AttributeName=SubmissionID,KeyType=HASH \
    --global-secondary-indexes \
        '[
            {
                "IndexName": "QuizID-Score-index",
                "KeySchema": [
                    {"AttributeName": "QuizID", "KeyType": "HASH"},
                    {"AttributeName": "Score", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
            }
        ]' \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

awslocal sqs create-queue --queue-name QuizSubmissionQueue

# Package functions

zip get_quiz_function.zip get_quiz_function.py
zip create_quiz_function.zip create_quiz_function.py
zip submit_quiz_function.zip submit_quiz_function.py
zip scoring_function.zip scoring_function.py
zip get_submission_function.zip get_submission_function.py
zip get_leaderboard_function.zip get_leaderboard_function.py

# Deploy Lambdas

# GetQuizFunction
awslocal lambda create-function \
    --function-name GetQuizFunction \
    --runtime python3.8 \
    --handler get_quiz_function.lambda_handler \
    --zip-file fileb://get_quiz_function.zip \
    --role arn:aws:iam::000000000000:role/DummyRole \
    --timeout 30

# CreateQuizFunction
awslocal lambda create-function \
    --function-name CreateQuizFunction \
    --runtime python3.8 \
    --handler create_quiz_function.lambda_handler \
    --zip-file fileb://create_quiz_function.zip \
    --role arn:aws:iam::000000000000:role/DummyRole \
    --timeout 30

# SubmitQuizFunction
awslocal lambda create-function \
    --function-name SubmitQuizFunction \
    --runtime python3.8 \
    --handler submit_quiz_function.lambda_handler \
    --zip-file fileb://submit_quiz_function.zip \
    --role arn:aws:iam::000000000000:role/DummyRole \
    --timeout 30

# ScoringFunction
awslocal lambda create-function \
    --function-name ScoringFunction \
    --runtime python3.8 \
    --handler scoring_function.lambda_handler \
    --zip-file fileb://scoring_function.zip \
    --role arn:aws:iam::000000000000:role/DummyRole \
    --timeout 30

# GetSubmissionFunction
awslocal lambda create-function \
    --function-name GetSubmissionFunction \
    --runtime python3.8 \
    --handler get_submission_function.lambda_handler \
    --zip-file fileb://get_submission_function.zip \
    --role arn:aws:iam::000000000000:role/DummyRole \
    --timeout 30

# GetLeaderboardFunction
awslocal lambda create-function \
    --function-name GetLeaderboardFunction \
    --runtime python3.8 \
    --handler get_leaderboard_function.lambda_handler \
    --zip-file fileb://get_leaderboard_function.zip \
    --role arn:aws:iam::000000000000:role/DummyRole \
    --timeout 30

# SQS Trigger

QUEUE_URL=$(awslocal sqs get-queue-url --queue-name QuizSubmissionQueue --query 'QueueUrl' --output text)
QUEUE_ARN=$(awslocal sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

awslocal lambda create-event-source-mapping \
    --function-name ScoringFunction \
    --batch-size 10 \
    --event-source-arn $QUEUE_ARN

# Create REST API

API_ID=$(awslocal apigateway create-rest-api \
    --name 'QuizAPI' \
    --query 'id' --output text)

# Get Root Resource ID

PARENT_ID=$(awslocal apigateway get-resources \
    --rest-api-id $API_ID \
    --query 'items[0].id' --output text)

# GetQuiz endpoint

RESOURCE_ID=$(awslocal apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PARENT_ID \
    --path-part getquiz \
    --query 'id' --output text)

awslocal apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --authorization-type "NONE"

awslocal apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:GetQuizFunction/invocations

# CreateQuiz endpoint

RESOURCE_ID=$(awslocal apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PARENT_ID \
    --path-part createquiz \
    --query 'id' --output text)

awslocal apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type "NONE"

awslocal apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:CreateQuizFunction/invocations

# SubmitQuiz endpoint

RESOURCE_ID=$(awslocal apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PARENT_ID \
    --path-part submitquiz \
    --query 'id' --output text)

awslocal apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type "NONE"

awslocal apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:SubmitQuizFunction/invocations

# Create GetSubmission endpoint
RESOURCE_ID=$(awslocal apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PARENT_ID \
    --path-part getsubmission \
    --query 'id' --output text)

awslocal apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --authorization-type "NONE"

awslocal apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:GetSubmissionFunction/invocations

# Create GetLeaderboard endpoint
RESOURCE_ID=$(awslocal apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PARENT_ID \
    --path-part getleaderboard \
    --query 'id' --output text)

awslocal apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --authorization-type "NONE"

awslocal apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:GetLeaderboardFunction/invocations

# Deploy

awslocal apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name test

# Get the ID and add it here

API_ENDPOINT="http://localhost:4566/restapis/$API_ID/test/_user_request_"

# Testing

# Create a quiz

curl -X POST "$API_ENDPOINT/createquiz" \
-H "Content-Type: application/json" \
-d '{
    "Title": "Sample Quiz",
    "Questions": [
        {
            "QuestionText": "What is the capital of France?",
            "Options": ["A. Berlin", "B. London", "C. Madrid", "D. Paris"],
            "CorrectAnswer": "D. Paris",
            "Trivia": "Paris is known as the City of Light."
        },
        {
            "QuestionText": "Who wrote Hamlet?",
            "Options": ["A. Dickens", "B. Shakespeare", "C. Twain", "D. Hemingway"],
            "CorrectAnswer": "B. Shakespeare",
            "Trivia": "Shakespeare is often called England national poet."
        }
    ]
}'

# Get the quiz; Change the ID below

curl -X GET "$API_ENDPOINT/getquiz?quiz_id=ab31c52b-17e6-42ab-a6a0-a9cd7c76ba59"

# Submit responses

curl -X POST "$API_ENDPOINT/submitquiz" \
-H "Content-Type: application/json" \
-d '{
    "Username": "user1",
    "QuizID": "ab31c52b-17e6-42ab-a6a0-a9cd7c76ba59",
    "Answers": {
        "0": "D. Paris",
        "1": "B. Shakespeare"
    }
}'

curl -X POST "$API_ENDPOINT/submitquiz" \
-H "Content-Type: application/json" \
-d '{
    "Username": "user2",
    "QuizID": "ab31c52b-17e6-42ab-a6a0-a9cd7c76ba59",
    "Answers": {
        "0": "A. Berlin",
        "1": "B. Shakespeare"
    }
}'

curl -X POST "$API_ENDPOINT/submitquiz" \
-H "Content-Type: application/json" \
-d '{
    "Username": "user3",
    "QuizID": "ab31c52b-17e6-42ab-a6a0-a9cd7c76ba59",
    "Answers": {
        "0": "D. Paris",
        "1": "D. Hemingway"
    }
}'

# Get submission

curl -X GET "$API_ENDPOINT/getsubmission?submission_id=102c1afb-9273-4a0f-956f-004affa8441b"

# Get leaderboard

curl -X GET "$API_ENDPOINT/getleaderboard?quiz_id=ab31c52b-17e6-42ab-a6a0-a9cd7c76ba59&top_n=3"

# SQS DLQ —> EventBridge Pipes —> SNS
# To test this, add:
# raise Exception("Simulated failure in ScoringFunction for testing SNS DLQ.")
# in the `scoring_function.py` file and update the Lambda.

SNS_TOPIC_ARN=$(awslocal sns create-topic --name DLQAlarmTopic --output json | jq -r '.TopicArn')
DLQ_URL=$(awslocal sqs create-queue --queue-name QuizSubmissionDLQ --output json | jq -r '.QueueUrl')
DLQ_ARN=$(awslocal sqs get-queue-attributes --queue-url $DLQ_URL --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

awslocal sqs set-queue-attributes \
    --queue-url $QUEUE_URL \
    --attributes '{
        "RedrivePolicy": "{\"deadLetterTargetArn\":\"'$DLQ_ARN'\",\"maxReceiveCount\":\"1\"}",
        "VisibilityTimeout": "10"
    }'

awslocal ses verify-email-identity --email your.email@example.com

awslocal sns subscribe \
    --topic-arn $SNS_TOPIC_ARN \
    --protocol email \
    --notification-endpoint your.email@example.com

awslocal pipes create-pipe \
  --name DLQToSNSPipe \
  --source $DLQ_ARN \
  --target $SNS_TOPIC_ARN \
  --role-arn arn:aws:iam::000000000000:role/DummyRole

awslocal sqs send-message \
    --queue-url $QUEUE_URL \
    --message-body '{"test": "message"}'

sleep 15

curl -s http://localhost.localstack.cloud:4566/_aws/ses
