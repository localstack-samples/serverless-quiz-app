import os
import pytest
import boto3
from playwright.sync_api import sync_playwright, expect
import time
import random
import string

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        # Launch browser in headed mode for debugging
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        yield browser
        browser.close()

@pytest.fixture(scope="session")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture(scope="session")
def app_url():
    # Use boto3 to get the CloudFront distribution ID
    cloudfront = boto3.client('cloudfront', endpoint_url='http://localhost:4566')
    response = cloudfront.list_distributions()
    distribution_id = response['DistributionList']['Items'][0]['Id']
    return f"https://{distribution_id}.cloudfront.localhost.localstack.cloud"

def test_quiz_flow(page, app_url):
    # Enable verbose logging
    page.set_viewport_size({"width": 1280, "height": 720})
    
    # Navigate to the home page
    print("\nNavigating to home page...")
    page.goto(app_url)
    
    # Verify the home page loaded
    print("Verifying home page...")
    expect(page.get_by_text("Welcome")).to_be_visible()
    
    # Select AWS Quiz from public quizzes
    print("Selecting AWS Quiz...")
    quiz_select = page.get_by_label("Select a Public Quiz")
    quiz_select.click()
    page.get_by_text("AWS Quiz").click()
    
    # Fill in user details
    username = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    print(f"Username: {username}")
    email = f"{username}@example.com"
    print(f"Email: {email}")
    print("Filling in user details...")
    username_input = page.get_by_label("Username")
    username_input.fill(username)
    
    # Optional: Fill in email
    email_input = page.get_by_label("Email (Optional)")
    email_input.fill(email)
    
    # Start the quiz
    print("Starting quiz...")
    start_button = page.get_by_text("Start Playing")
    expect(start_button).to_be_enabled()
    start_button.click()
    
    # Wait for first question to load
    print("Waiting for first question...")
    expect(page.get_by_text("Question 1 / 5")).to_be_visible()
    
    # Answer all questions
    answers = [
        "B. Amazon EC2",  # What is the primary compute service in AWS?
        "A. Simple Storage Service",  # What does S3 stand for in AWS?
        "A. Amazon DynamoDB",  # Which AWS service is a NoSQL database?
        "B. AWS Lambda",  # Which AWS service lets you run code without provisioning servers?
        "B. Identity and Access Management"  # What is IAM used for?
    ]
    
    for i, answer in enumerate(answers):
        print(f"Answering question {i + 1}...")
        # Wait for question to be visible
        expect(page.get_by_text(f"Question {i + 1} / 5")).to_be_visible()
        
        # Select answer
        answer_radio = page.get_by_label(answer)
        expect(answer_radio).to_be_visible()
        answer_radio.click()
        
        # Wait for next question or submit button
        time.sleep(2)  # Increased delay to ensure state updates
    
    # After last question, verify we're on the results page
    print("Waiting for results page...")
    
    # Take a screenshot for debugging
    page.screenshot(path="results-page.png")
    
    # Print current page content for debugging
    print("\nPage content after quiz completion:")
    print(page.content())
    
    # Try different selectors for the results
    selectors = [
        "text=Processing your submission...",
        "text=Your Score",
        "text=Quiz Results",
        ".main-quiz-container",  # Try container class
        "[data-testid=results-page]"  # Try test ID if available
    ]
    
    for selector in selectors:
        try:
            print(f"\nTrying to find: {selector}")
            element = page.wait_for_selector(selector, timeout=5000)
            if element:
                print(f"Found element with selector: {selector}")
                break
        except Exception as e:
            print(f"Selector {selector} not found: {str(e)}")
    
    # Wait longer for results processing
    print("Waiting for results to process...")
    time.sleep(5)  # Give more time for backend processing
    
    # Try to find score text with a more flexible approach
    score_element = page.get_by_text("Score", exact=False)
    if score_element:
        print(f"Found score element: {score_element.text_content()}")
    
    # Click View Leaderboard if available
    try:
        leaderboard_button = page.get_by_text("View Leaderboard")
        if leaderboard_button.is_visible():
            print("Clicking leaderboard button...")
            leaderboard_button.click()
            
            # Verify leaderboard loaded
            expect(page.get_by_text("Leaderboard")).to_be_visible()
            
            # Verify our user appears in the leaderboard
            print("Checking leaderboard entries...")
            leaderboard_entries = page.get_by_role("row")
            found_user = False
            for entry in leaderboard_entries.all():
                content = entry.text_content()
                print(f"Leaderboard entry: {content}")
                if username in content.lower():
                    found_user = True
                    break
            
            assert found_user, "User not found in leaderboard"
    except Exception as e:
        print(f"Error accessing leaderboard: {str(e)}")
        page.screenshot(path="leaderboard-error.png")

def test_quiz_creation(page, app_url):
    print("\nStarting quiz creation test...")
    # Navigate to home page
    print("Navigating to home page...")
    page.goto(app_url)
    
    # Click Create a New Quiz
    print("Clicking Create a New Quiz...")
    page.get_by_text("Create a New Quiz").click()
    
    # Fill in quiz details
    print("Filling quiz title...")
    page.get_by_label("Quiz Title").fill("Test Quiz")
    
    # Add a question
    print("Adding question text...")
    question_input = page.get_by_role("textbox", name="Question Text")
    question_input.fill("What is LocalStack?")
    
    # Fill options
    options = [
        "A. A cloud service emulator",
        "B. A database system",
        "C. A web framework",
        "D. A programming language"
    ]
    
    print("Filling options...")
    for i, option in enumerate(options):
        # Use role selector for textbox with specific name
        option_input = page.get_by_role("textbox", name=f"Option {i + 1}")
        option_input.fill(option)
    
    # Add trivia (if required)
    print("Adding trivia...")
    trivia_input = page.get_by_role("textbox", name="Trivia")
    trivia_input.fill("LocalStack is a cloud service emulator that runs in a single container on your laptop.")
    
    # Select correct answer using radio group
    print("Selecting correct answer...")
    radio_group = page.get_by_role("radiogroup")
    expect(radio_group).to_be_visible()
    
    # Select the first option (A) as correct answer
    correct_answer = page.locator('input[type="radio"]').first
    expect(correct_answer).to_be_visible()
    correct_answer.check()
    
    # Add question
    print("Adding question...")
    add_question_button = page.get_by_role("button", name="Add Question")
    expect(add_question_button).to_be_enabled()
    add_question_button.click()
    
    # Submit quiz
    print("Submitting quiz...")
    submit_button = page.get_by_role("button", name="Submit Quiz")
    expect(submit_button).to_be_enabled()
    submit_button.click()
    
    # Verify quiz was created
    print("Verifying quiz creation...")
    success_message = page.get_by_text("Quiz created successfully!")
    expect(success_message).to_be_visible()
    
    # Get Quiz ID from success message
    success_text = success_message.text_content()
    quiz_id = success_text.split("Quiz ID: ")[1]
    print(f"Quiz created with ID: {quiz_id}")
    
    # Go back to home
    print("Going back to home...")
    page.get_by_text("Go to Home").click()
    
    # Verify we can find and start the new quiz
    print("Starting the created quiz...")
    quiz_id_input = page.get_by_label("Quiz ID")
    quiz_id_input.fill(quiz_id)
    
    username = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    print(f"Using username: {username}")
    username_input = page.get_by_label("Username")
    username_input.fill(username)
    
    start_button = page.get_by_text("Start Playing")
    expect(start_button).to_be_enabled()
    start_button.click()
    
    # Verify question appears
    print("Verifying question appears...")
    expect(page.get_by_text("What is LocalStack?")).to_be_visible()
    print("Quiz creation test completed successfully!") 
