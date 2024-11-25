import pytest
import time
import boto3
import json
import requests

import localstack.sdk.chaos
from localstack.sdk.models import FaultRule
from localstack.sdk.chaos.managers import fault_configuration

LOCALSTACK_ENDPOINT = "http://localhost.localstack.cloud:4566"
API_NAME = 'QuizAPI'

class TestLocalStackClient:
    client = localstack.sdk.chaos.ChaosClient()

@pytest.fixture(scope='module')
def apigateway_client():
    return boto3.client('apigateway', endpoint_url=LOCALSTACK_ENDPOINT)

@pytest.fixture(scope='module')
def api_endpoint(apigateway_client):
    response = apigateway_client.get_rest_apis()
    api_list = response.get('items', [])
    api = next((item for item in api_list if item['name'] == API_NAME), None)

    if not api:
        raise Exception(f"API {API_NAME} not found.")

    API_ID = api['id']
    API_ENDPOINT = f"{LOCALSTACK_ENDPOINT}/_aws/execute-api/{API_ID}/test"

    print(f"API Endpoint: {API_ENDPOINT}")

    time.sleep(2)

    return API_ENDPOINT

def test_dynamodb_outage(api_endpoint):
    outage_rule = FaultRule(region="us-east-1", service="dynamodb")

    # Using fault_configuration context manager to apply and automatically clean up the fault rule
    with fault_configuration(fault_rules=[outage_rule]):
        print("DynamoDB outage initiated within context.")

        # Attempt to create a quiz during the outage
        create_quiz_payload = {
            "Title": "Outage Test Quiz",
            "Visibility": "Public",
            "EnableTimer": False,
            "Questions": [
                {
                    "QuestionText": "What is the capital of Spain?",
                    "Options": ["A. Lisbon", "B. Madrid", "C. Barcelona", "D. Valencia"],
                    "CorrectAnswer": "B. Madrid",
                    "Trivia": "Madrid is the capital and largest city of Spain."
                }
            ]
        }

        response = requests.post(
            f"{api_endpoint}/createquiz",
            headers={"Content-Type": "application/json"},
            data=json.dumps(create_quiz_payload)
        )

        # Expecting a 500 error due to the outage
        assert response.status_code == 500
        response_data = response.json()
        assert "Error storing quiz data. It has been queued for retry." in response_data.get("message", "")
        print("Received expected error message during outage.")

    # After the context manager exits, the outage should be resolved
    print("Waiting for the system to process the queued request...")
    time.sleep(15)

    # Check if the quiz was eventually created successfully
    response = requests.get(f"{api_endpoint}/listquizzes")
    assert response.status_code == 200
    quizzes_list = response.json().get('Quizzes', [])
    quiz_titles = [quiz['Title'] for quiz in quizzes_list]
    assert "Outage Test Quiz" in quiz_titles
    print("Quiz successfully created after outage resolved.")
