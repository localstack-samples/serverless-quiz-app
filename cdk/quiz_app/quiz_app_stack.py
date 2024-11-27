import json
from pathlib import Path
from tty import CFLAG

import aws_cdk
from aws_cdk import (
    # Duration,
    Stack,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_sns as sns,
    aws_stepfunctions as sfn,
    aws_pipes as pipes,
    aws_sqs as sqs,
    custom_resources as cr,
    CfnOutput as Output,
)
from constructs import Construct


class QuizAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TABLES
        quizzes_table = dynamodb.Table(
            self,
            "QuizzesTable",
            table_name="Quizzes",
            partition_key=dynamodb.Attribute(
                name="QuizID",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=5,
        )

        user_submissions_table = dynamodb.Table(
            self,
            "UserSubmissionsTable",
            table_name="UserSubmissions",
            partition_key=dynamodb.Attribute(
                name="SubmissionID",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=5,
        )
        user_submissions_table.add_global_secondary_index(
            index_name="QuizID-Score-index",
            partition_key=dynamodb.Attribute(
                name="QuizID",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="Score",
                type=dynamodb.AttributeType.NUMBER,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
            read_capacity=5,
            write_capacity=5,
        )

        dlq_submission_queue = sqs.Queue(self, "QuizSubmissionDLQ")
        submission_queue = sqs.Queue(
            self,
            "QuizSubmissionQueue",
            queue_name="QuizSubmissionQueue",
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=1, queue=dlq_submission_queue
            ),
            visibility_timeout=aws_cdk.Duration.seconds(10),
        )
        functions_and_roles = [
            (
                "CreateQuizFunction",
                "configurations/create_quiz_policy.json",
                "CreateQuizRole",
                "lambdas/get_quiz",
            ),
            (
                "GetQuizFunction",
                "configurations/get_quiz_policy.json",
                "GetQuizRole",
                "lambdas/get_quiz",
            ),
            (
                "SubmitQuizFunction",
                "configurations/submit_quiz_policy.json",
                "SubmitQuizRole",
                "lambdas/submit_quiz",
            ),
            (
                "ScoringFunction",
                "configurations/scoring_policy.json",
                "ScoringRole",
                "lambdas/scoring",
            ),
            (
                "GetSubmissionFunction",
                "configurations/get_submission_policy.json",
                "GetSubmissionRole",
                "lambdas/get_submission",
            ),
            (
                "GetLeaderboardFunction",
                "configurations/get_leaderboard_policy.json",
                "GetLeaderboardRole",
                "lambdas/get_leaderboard",
            ),
            (
                "ListPublicQuizzesFunction",
                "configurations/list_quizzes_policy.json",
                "ListQuizzesRole",
                "lambdas/list_quizzes",
            ),
            (
                "RetryQuizzesWritesFunction",
                "configurations/retry_quizzes_writes_policy.json",
                "RetryQuizzesWritesRole",
                "lambdas/retry_quizzes_writes",
            ),
        ]
        functions = {}

        for function_info in functions_and_roles:
            function_name, policy_file_path, role_name, handler_path = function_info
            policy_json = self.read_policy_file(f"../{policy_file_path}")
            policy_document = iam.PolicyDocument.from_json(policy_json)

            policy = iam.ManagedPolicy(
                self,
                f"{function_name}FunctionPolicy",
                managed_policy_name=f"{function_name}Policy",
                document=policy_document,
            )

            role = iam.Role(
                self,
                f"{function_name}LambdaExecutionRole",
                role_name=role_name,
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                description=f"Role for Lambda function {function_name}",
            )

            # Attach the policy to the role
            role.add_managed_policy(policy)

            current_function = _lambda.Function(
                self,
                f"{function_name}LambdaFunction",
                function_name=function_name,
                runtime=_lambda.Runtime.PYTHON_3_11,
                handler="handler.lambda_handler",
                code=_lambda.Code.from_asset(f"../{handler_path}"),
                role=role,
                timeout=aws_cdk.Duration.seconds(30),
            )
            functions[function_name] = current_function

        submission_queue.grant_consume_messages(functions["ScoringFunction"])
        _lambda.EventSourceMapping(
            self,
            "ScoringFunctionSubscription",
            target=functions["ScoringFunction"],
            event_source_arn=submission_queue.queue_arn,
        )

        # create rest api
        rest_api = apigateway.RestApi(self, "QuizAPI")
        endpoints = [
            ("getquiz", "GET", "GetQuizFunction"),
            ("createquiz", "POST", "CreateQuizFunction"),
            ("submitquiz", "POST", "SubmitQuizFunction"),
            ("getsubmission", "GET", "GetSubmissionFunction"),
            ("getleaderboard", "GET", "GetLeaderboardFunction"),
            ("listquizzes", "GET", "ListPublicQuizzesFunction"),
        ]
        for path_part, http_method, function_name in endpoints:
            resource = rest_api.root.add_resource(path_part)
            integration = apigateway.LambdaIntegration(
                functions[function_name], proxy=True
            )
            resource.add_method(http_method, integration=integration)

        # verify email identity for SES
        for email in ["your.email@example.com", "admin@localstack.cloud"]:
            sanitised_email = email.replace(".", "-").replace("@", "-")
            cr.AwsCustomResource(
                self,
                f"EmailVerifier{sanitised_email}",
                on_update=cr.AwsSdkCall(
                    service="SES",
                    action="VerifyEmailIdentity",
                    parameters={
                        "EmailAddress": email,
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(
                        f"verify-{sanitised_email}"
                    ),
                ),
                policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                    resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE,
                ),
            )

        dlq_alarm_topic = sns.Topic(self, "DLQAlarmTopic")
        dlq_alarm_topic.add_subscription(
            aws_cdk.aws_sns_subscriptions.EmailSubscription(
                email_address="your.email@example.com",
            )
        )

        # eventbridge pipe
        policy_document = iam.PolicyDocument.from_json(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "sqs:ReceiveMessage",
                            "sqs:DeleteMessage",
                            "sqs:GetQueueAttributes",
                            "sqs:GetQueueUrl",
                        ],
                        "Resource": dlq_submission_queue.queue_arn,
                    },
                    {
                        "Effect": "Allow",
                        "Action": "sns:Publish",
                        "Resource": dlq_alarm_topic.topic_arn,
                    },
                ],
            }
        )
        policy = iam.ManagedPolicy(
            self,
            "PipesPolicy",
            document=policy_document,
        )
        pipes_role = iam.Role(
            self,
            f"PipeRole",
            assumed_by=iam.ServicePrincipal("pipes.amazonaws.com"),
            managed_policies=[policy],
        )
        pipe = pipes.CfnPipe(
            self,
            "DLQToSNSPipe",
            source=dlq_submission_queue.queue_arn,
            target=dlq_alarm_topic.topic_arn,
            role_arn=pipes_role.role_arn,
        )

        # state machine

        policy_document = iam.PolicyDocument.from_json(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ses:SendEmail",
                            "ses:SendRawEmail",
                            "sesv2:SendEmail",
                        ],
                        "Resource": "*",
                    }
                ],
            }
        )
        policy = iam.ManagedPolicy(
            self, "SendEmailStateMachinePolicy", document=policy_document
        )
        state_machine_role = iam.Role(
            self,
            "SendEmailStateMachineRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            managed_policies=[policy],
        )

        self.state_machine = sfn.StateMachine(
            self,
            "SendEmailStateMachine",
            definition_body=sfn.DefinitionBody.from_file(
                "../configurations/statemachine.json"
            ),
            role=state_machine_role,
        )

    @staticmethod
    def read_policy_file(file_path: str) -> dict:
        """Reads a JSON policy file and returns it as a dictionary."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")
        with open(file_path, "r") as file:
            return json.load(file)
