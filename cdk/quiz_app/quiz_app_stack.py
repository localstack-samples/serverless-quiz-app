import aws_cdk
from aws_cdk import (
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
)
from constructs import Construct


class QuizAppStack(Stack):
    backend_api_url: str

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
            visibility_timeout=aws_cdk.Duration.minutes(1),
        )
        functions_and_roles = [
            (
                "CreateQuizFunction",
                "lambdas/create_quiz",
            ),
            (
                "GetQuizFunction",
                "lambdas/get_quiz",
            ),
            (
                "SubmitQuizFunction",
                "lambdas/submit_quiz",
            ),
            (
                "ScoringFunction",
                "lambdas/scoring",
            ),
            (
                "GetSubmissionFunction",
                "lambdas/get_submission",
            ),
            (
                "GetLeaderboardFunction",
                "lambdas/get_leaderboard",
            ),
            (
                "ListPublicQuizzesFunction",
                "lambdas/list_quizzes",
            ),
            (
                "RetryQuizzesWritesFunction",
                "lambdas/retry_quizzes_writes",
            ),
        ]
        functions = {}

        for function_info in functions_and_roles:
            function_name, handler_path = function_info
            current_function = _lambda.Function(
                self,
                f"{function_name}LambdaFunction",
                function_name=function_name,
                runtime=_lambda.Runtime.PYTHON_3_11,
                handler="handler.lambda_handler",
                code=_lambda.Code.from_asset(f"../{handler_path}"),
                timeout=aws_cdk.Duration.seconds(30),
            )
            functions[function_name] = current_function

        _lambda.EventSourceMapping(
            self,
            "ScoringFunctionSubscription",
            target=functions["ScoringFunction"],
            event_source_arn=submission_queue.queue_arn,
        )

        # create rest api
        # TODO: this is a circular dependency as we need to know the cloudfront
        # domain name from the FrontendStack to add a specific origin, but the
        # FrontendStack depends on the APIGW URL from this stack
        rest_api = apigateway.RestApi(
            self,
            "QuizAPI",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            ),
        )

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

        self.backend_api_url = rest_api.url

        # verify email identity for SES
        for email in ["your.email@example.com", "admin@localstack.cloud", "sender@example.com"]:
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
            state_machine_name="SendEmailStateMachine"
        )

        # set up lambda permissions
        quizzes_table.grant_write_data(functions["CreateQuizFunction"])
        # TODO: createquizfunction should be able to write to QuizzesWriteFailures
        quizzes_table.grant_read_data(functions["GetQuizFunction"])
        quizzes_table.grant_read_data(functions["SubmitQuizFunction"])
        submission_queue.grant_send_messages(functions["SubmitQuizFunction"])
        quizzes_table.grant_read_write_data(functions["ScoringFunction"])
        self.state_machine.grant_start_execution(functions["ScoringFunction"])
        submission_queue.grant_consume_messages(functions["ScoringFunction"])
        user_submissions_table.grant_read_write_data(functions["ScoringFunction"])
        user_submissions_table.grant_read_data(functions["GetSubmissionFunction"])
        user_submissions_table.grant_read_data(functions["GetLeaderboardFunction"])
        quizzes_table.grant_read_data(functions["ListPublicQuizzesFunction"])
        quizzes_table.grant_read_write_data(functions["RetryQuizzesWritesFunction"])
        # TODO: retryquizzeswritesfunction should have access to read and write to quizzeswritefailuresqueue
