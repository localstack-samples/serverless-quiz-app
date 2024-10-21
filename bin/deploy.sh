#!/bin/bash


# Create DynamoDB tables
awslocal dynamodb create-table \
    --table-name Quizzes \
    --attribute-definitions AttributeName=QuizID,AttributeType=S \
    --key-schema AttributeName=QuizID,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --output text

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
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --output text

awslocal sqs create-queue --queue-name QuizSubmissionQueue

# Zip Lambda functions
zip -j get_quiz_function.zip lambdas/get_quiz/handler.py
zip -j create_quiz_function.zip lambdas/create_quiz/handler.py
zip -j submit_quiz_function.zip lambdas/submit_quiz/handler.py
zip -j scoring_function.zip lambdas/scoring/handler.py
zip -j get_submission_function.zip lambdas/get_submission/handler.py
zip -j get_leaderboard_function.zip lambdas/get_leaderboard/handler.py
zip -j list_quizzes_function.zip lambdas/list_quizzes/handler.py
zip -j retry_quizzes_writes_function.zip lambdas/retry_quizzes_writes/handler.py

# Function names and their policy files
FUNCTIONS=(
  "CreateQuizFunction configurations/create_quiz_policy.json CreateQuizRole"
  "GetQuizFunction configurations/get_quiz_policy.json GetQuizRole"
  "SubmitQuizFunction configurations/submit_quiz_policy.json SubmitQuizRole"
  "ScoringFunction configurations/scoring_policy.json ScoringRole"
  "GetSubmissionFunction configurations/get_submission_policy.json GetSubmissionRole"
  "GetLeaderboardFunction configurations/get_leaderboard_policy.json GetLeaderboardRole"
  "ListPublicQuizzesFunction configurations/list_quizzes_policy.json ListQuizzesRole"
  "RetryQuizzesWritesFunction configurations/retry_quizzes_writes_policy.json RetryQuizzesWritesRole"
)

# Create IAM policies and roles
for FUNCTION_INFO in "${FUNCTIONS[@]}"; do
  read FUNCTION_NAME POLICY_FILE ROLE_NAME <<< "$FUNCTION_INFO"
  
  # Create IAM Policy
  awslocal iam create-policy \
      --policy-name ${FUNCTION_NAME}Policy \
      --policy-document file://${POLICY_FILE}
  
  # Create IAM Role
  ROLE_ARN=$(awslocal iam create-role \
      --role-name ${ROLE_NAME} \
      --assume-role-policy-document file://configurations/lambda_trust_policy.json \
      --query 'Role.Arn' --output text)
  
  # Attach Policy to Role
  awslocal iam attach-role-policy \
      --role-name ${ROLE_NAME} \
      --policy-arn arn:aws:iam::000000000000:policy/${FUNCTION_NAME}Policy
done

# Create IAM Policy for State Machine
awslocal iam create-policy \
    --policy-name SendEmailStateMachinePolicy \
    --policy-document file://configurations/state_machine_policy.json

# Create IAM Role for State Machine
awslocal iam create-role \
    --role-name SendEmailStateMachineRole \
    --assume-role-policy-document file://configurations/state_machine_trust_policy.json

# Attach Policy to Role
awslocal iam attach-role-policy \
    --role-name SendEmailStateMachineRole \
    --policy-arn arn:aws:iam::000000000000:policy/SendEmailStateMachinePolicy

# Deploy Lambdas

# CreateQuizFunction
awslocal lambda create-function \
    --function-name CreateQuizFunction \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb://create_quiz_function.zip \
    --role arn:aws:iam::000000000000:role/CreateQuizRole \
    --timeout 30 \
    --output text

# GetQuizFunction
awslocal lambda create-function \
    --function-name GetQuizFunction \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb://get_quiz_function.zip \
    --role arn:aws:iam::000000000000:role/GetQuizRole \
    --timeout 30 \
    --output text

# SubmitQuizFunction
awslocal lambda create-function \
    --function-name SubmitQuizFunction \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb://submit_quiz_function.zip \
    --role arn:aws:iam::000000000000:role/SubmitQuizRole \
    --timeout 30 \
    --output text

# ScoringFunction
awslocal lambda create-function \
    --function-name ScoringFunction \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb://scoring_function.zip \
    --role arn:aws:iam::000000000000:role/ScoringRole \
    --timeout 30 \
    --output text

# GetSubmissionFunction
awslocal lambda create-function \
    --function-name GetSubmissionFunction \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb://get_submission_function.zip \
    --role arn:aws:iam::000000000000:role/GetSubmissionRole \
    --timeout 30 \
    --output text

# GetLeaderboardFunction
awslocal lambda create-function \
    --function-name GetLeaderboardFunction \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb://get_leaderboard_function.zip \
    --role arn:aws:iam::000000000000:role/GetLeaderboardRole \
    --timeout 30 \
    --output text

# ListPublicQuizzesFunction
awslocal lambda create-function \
    --function-name ListPublicQuizzesFunction \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb://list_quizzes_function.zip \
    --role arn:aws:iam::000000000000:role/ListQuizzesRole \
    --timeout 30 \
    --output text

# RetryQuizzesWritesFunction
awslocal lambda create-function \
    --function-name RetryQuizzesWritesFunction \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb://retry_quizzes_writes_function.zip \
    --role arn:aws:iam::000000000000:role/RetryQuizzesWritesRole \
    --timeout 30 \
    --output text

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

# ListQuizzes endpoint

RESOURCE_ID=$(awslocal apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PARENT_ID \
    --path-part listquizzes \
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
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:ListPublicQuizzesFunction/invocations

# Deploy

awslocal apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name test

API_ENDPOINT="http://localhost:4566/restapis/$API_ID/test/_user_request_"


# SQS DLQ —> EventBridge Pipes —> SNS
# To test this, add:
# raise Exception("Simulated failure in ScoringFunction for testing SNS DLQ.")
# in the `scoring_function.py` file and update the Lambda.
SNS_TOPIC_ARN=$(awslocal sns create-topic --name DLQAlarmTopic --output json | jq -r '.TopicArn')
DLQ_URL=$(awslocal sqs create-queue --queue-name QuizSubmissionDLQ --output json | jq -r '.QueueUrl')
DLQ_ARN=$(awslocal sqs get-queue-attributes --queue-url $DLQ_URL --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

# Configure SQS Redrive Policy
awslocal sqs set-queue-attributes \
    --queue-url $QUEUE_URL \
    --attributes '{
        "RedrivePolicy": "{\"deadLetterTargetArn\":\"'$DLQ_ARN'\",\"maxReceiveCount\":\"1\"}",
        "VisibilityTimeout": "10"
    }'

# Verify Email Identity for SES
awslocal ses verify-email-identity --email your.email@example.com

# Subscribe Email to SNS Topic
awslocal sns subscribe \
    --topic-arn $SNS_TOPIC_ARN \
    --protocol email \
    --notification-endpoint your.email@example.com

# Create IAM Role for Pipe
awslocal iam create-role \
    --role-name PipeRole \
    --assume-role-policy-document file://configurations/pipe_role_trust_policy.json

# Attach Policy to Role
awslocal iam put-role-policy \
    --role-name PipeRole \
    --policy-name PipePolicy \
    --policy-document file://configurations/pipe_role_policy.json

# Create EventBridge Pipe
awslocal pipes create-pipe \
  --name DLQToSNSPipe \
  --source $DLQ_ARN \
  --target $SNS_TOPIC_ARN \
  --role-arn arn:aws:iam::000000000000:role/PipeRole

# Create State Machine
awslocal stepfunctions create-state-machine \
    --name SendEmailStateMachine \
    --definition file://configurations/statemachine.json \
    --role-arn arn:aws:iam::000000000000:role/SendEmailStateMachineRole

echo $API_ENDPOINT

# Deploy Frontend
pushd frontend
npm install
npm run build
awslocal s3 mb s3://webapp
awslocal s3 sync --delete ./build s3://webapp
awslocal s3 website s3://webapp --index-document index.html --error-document index.html
popd

# Create CloudFront Distribution
DISTRIBUTION=$(awslocal cloudfront create-distribution --distribution-config file://configurations/distribution-config.json)
DOMAIN_NAME=$(echo "$DISTRIBUTION" | jq -r '.Distribution.DomainName')
echo $DOMAIN_NAME

# Setup Chaos Testing
awslocal sns create-topic --name QuizzesWriteFailures --output json

WRITE_FAILURES_QUEUE_URL=$(awslocal sqs create-queue --queue-name QuizzesWriteFailuresQueue --attributes VisibilityTimeout=60 --output json | jq -r '.QueueUrl')
WRITE_FAILURES_QUEUE_ARN=$(awslocal sqs get-queue-attributes --queue-url $WRITE_FAILURES_QUEUE_URL --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

awslocal sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:000000000000:QuizzesWriteFailures \
    --protocol sqs \
    --notification-endpoint $WRITE_FAILURES_QUEUE_ARN \
    --output text

awslocal lambda create-event-source-mapping \
    --function-name RetryQuizzesWritesFunction \
    --batch-size 10 \
    --event-source-arn $WRITE_FAILURES_QUEUE_ARN \
    --enabled \
    --output text

# API Gateway permissions

API_NAME="QuizAPI"

API_ID=$(awslocal apigateway get-rest-apis \
  --query "items[?name=='$API_NAME'].id" \
  --output text)

awslocal lambda add-permission \
    --function-name CreateQuizFunction \
    --statement-id AllowAPIGatewayInvoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:000000000000:${API_ID}/*/POST/createquiz"

awslocal lambda add-permission \
    --function-name SubmitQuizFunction \
    --statement-id AllowAPIGatewayInvoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:000000000000:${API_ID}/*/POST/submitquiz"

awslocal lambda add-permission \
    --function-name GetQuizFunction \
    --statement-id AllowAPIGatewayInvoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:000000000000:${API_ID}/*/GET/getquiz"

awslocal lambda add-permission \
    --function-name GetSubmissionFunction \
    --statement-id AllowAPIGatewayInvoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:000000000000:${API_ID}/*/GET/getsubmission"

awslocal lambda add-permission \
    --function-name GetLeaderboardFunction \
    --statement-id AllowAPIGatewayInvoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:000000000000:${API_ID}/*/GET/getleaderboard"

awslocal lambda add-permission \
    --function-name ListPublicQuizzesFunction \
    --statement-id AllowAPIGatewayInvoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:000000000000:${API_ID}/*/GET/listquizzes"

QUEUE_URL=$(awslocal sqs get-queue-url --queue-name QuizzesWriteFailuresQueue --output text --query QueueUrl)

policy_json=$(cat configurations/sqs_queue_policy.json | jq -c . | jq -R .)

awslocal sqs set-queue-attributes --queue-url "$QUEUE_URL" --attributes "{\"Policy\":$policy_json}"

awslocal sqs get-queue-attributes --queue-url "$QUEUE_URL" --attribute-names All

# Cleanup

rm *.zip