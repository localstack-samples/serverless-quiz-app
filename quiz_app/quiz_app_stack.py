import json
from pathlib import Path
from tty import CFLAG

import aws_cdk
from aws_cdk import (
    # Duration,
    Stack,
    aws_sqs as sqs,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
    CfnOutput as Output
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

        functions_and_roles = [
            ("CreateQuizFunction","configurations/create_quiz_policy.json","CreateQuizRole", "lambdas/get_quiz"),
            ("GetQuizFunction","configurations/get_quiz_policy.json","GetQuizRole", "lambdas/get_quiz"),
            ("SubmitQuizFunction","configurations/submit_quiz_policy.json", "SubmitQuizRole", "lambdas/submit_quiz"),
            ("ScoringFunction", "configurations/scoring_policy.json", "ScoringRole", "lambdas/scoring"),
            ("GetSubmissionFunction", "configurations/get_submission_policy.json", "GetSubmissionRole", "lambdas/get_submission"),
            ("GetLeaderboardFunction", "configurations/get_leaderboard_policy.json", "GetLeaderboardRole", "lambdas/get_leaderboard"),
            ("ListPublicQuizzesFunction", "configurations/list_quizzes_policy.json", "ListQuizzesRole", "lambdas/list_quizzes"),
            ("RetryQuizzesWritesFunction","configurations/retry_quizzes_writes_policy.json", "RetryQuizzesWritesRole", "lambdas/retry_quizzes_writes"),
        ]

        for function_info in functions_and_roles:

            function_name, policy_file_path,  role_name, handler_path = function_info
            policy_json = self.read_policy_file(f"./{policy_file_path}")
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

            _lambda.Function(
                self,
                f"{function_name}LambdaFunction",
                function_name=function_name,
                runtime=_lambda.Runtime.PYTHON_3_11,
                handler="handler.lambda_handler",
                code=_lambda.Code.from_asset(handler_path),
                role=role,
                timeout=aws_cdk.Duration.seconds(30),
            )

        sqs.Queue(self, "QuizSubmissionQueue", queue_name="QuizSubmissionQueue")

    @staticmethod
    def read_policy_file(file_path: str) -> dict:
        """Reads a JSON policy file and returns it as a dictionary."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")
        with open(file_path, "r") as file:
            return json.load(file)
