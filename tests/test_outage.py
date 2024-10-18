import pytest
import time
import boto3
import requests
import json

LOCALSTACK_ENDPOINT = "http://localhost:4566"
CHAOS_ENDPOINT = f"{LOCALSTACK_ENDPOINT}/_localstack/chaos/faults"
API_NAME = 'QuizAPI'

@pytest.fixture(scope='module')
def api_endpoint():
    apigateway_client = boto3.client('apigateway', endpoint_url=LOCALSTACK_ENDPOINT)
    response = apigateway_client.get_rest_apis()
    api_list = response.get('items', [])
    api = next((item for item in api_list if item['name'] == API_NAME), None)

    if not api:
        raise Exception(f"API {API_NAME} not found.")

    API_ID = api['id']
    API_ENDPOINT = f"{LOCALSTACK_ENDPOINT}/restapis/{API_ID}/test/_user_request_"

    print(f"API Endpoint: {API_ENDPOINT}")

    time.sleep(2)

    return API_ENDPOINT

def initiate_dynamodb_outage():
    outage_payload = [{"service": "dynamodb", "region": "us-east-1"}]
    response = requests.post(CHAOS_ENDPOINT, json=outage_payload)
    assert response.ok, "Failed to initiate DynamoDB outage"
    print("DynamoDB outage initiated.")
    return outage_payload

def check_outage_status(expected_status):
    response = requests.get(CHAOS_ENDPOINT)
    assert response.ok, "Failed to get outage status"
    outage_status = response.json()
    assert outage_status == expected_status, "Outage status does not match expected status"

def stop_dynamodb_outage():
    response = requests.post(CHAOS_ENDPOINT, json=[])
    assert response.ok, "Failed to stop DynamoDB outage"
    check_outage_status([])
    print("DynamoDB outage stopped.")

def test_dynamodb_outage(api_endpoint):
    outage_payload = initiate_dynamodb_outage()

    try:
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

        assert response.status_code == 500
        response_data = response.json()
        assert "Error storing quiz data. It has been queued for retry." in response_data.get("message", "")
        print("Received expected error message during outage.")

        check_outage_status(outage_payload)

    finally:
        stop_dynamodb_outage()

    print("Waiting for the system to process the queued request...")
    time.sleep(15)

    response = requests.get(f"{api_endpoint}/listquizzes")
    assert response.status_code == 200
    quizzes_list = response.json().get('Quizzes', [])
    quiz_titles = [quiz['Title'] for quiz in quizzes_list]
    assert "Outage Test Quiz" in quiz_titles
    print("Quiz successfully created after outage resolved.")
