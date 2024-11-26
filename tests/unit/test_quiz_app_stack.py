import aws_cdk as core
import aws_cdk.assertions as assertions

from quiz_app.quiz_app_stack import QuizAppStack

# example tests. To run these tests, uncomment this file along with the example
# resource in quiz_app/quiz_app_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = QuizAppStack(app, "quiz-app")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
