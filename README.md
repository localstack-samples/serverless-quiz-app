# Serverless Quiz App

This project showcases a fully serverless quiz application designed to demonstrate LocalStack's capabilities in supporting local cloud development, debugging, and testing throughout the entire software development lifecycle (SDLC).
The application enables users to create quizzes, participate by submitting answers, and view leaderboards for top scores.
It leverages various LocalStack features to highlight the platform's capabilities, including:

-   Emulating cloud environments locally with **Core Cloud Emulator**.
-   Utilizing **Resource Browsers** for inspecting local resources.
-   Gaining insights into your development environment with **Stack Insights**.
-   Integrating continuous testing with **LocalStack GitHub Actions** and **SDK**.
-   Streaming security policies to refine access controls with **IAM Policy Stream**.
-   Managing state snapshots and injecting resource state with **Cloud Pods**.
-   Implementing chaos engineering to test system resilience with **Chaos API**.
-   Utilizing **Ephemeral Instances** for temporary, isolated testing environments.
-   Extending functionality with **LocalStack Extensions** for enhanced development workflows.

## Architecture

![Application Architecture](images/architecture.png)

The following resources are being deployed:

-   **DynamoDB**: Stores quiz metadata in `Quizzes` and user data in `UserSubmissions` with indexing for leaderboards.
-   **SQS**: Manages async submissions via `QuizSubmissionQueue`, with a DLQ for failed messages.
-   **Lambda**: Executes serverless functions for creating, submitting, scoring, and fetching quizzes.
-   **IAM**: Defines roles and policies to grant Lambdas and state machines access to necessary resources.
-   **API Gateway**: Exposes REST endpoints for quiz operations, linking HTTP methods to Lambda functions.
-   **SNS**: Sends alerts via `DLQAlarmTopic` and triggers `QuizzesWriteFailures` for chaos testing.
-   **EventBridge Pipes**: Connects `QuizSubmissionDLQ` to SNS to handle dead-letter queue notifications.
-   **Step Functions**: Manages email notification workflows with `SendEmailStateMachine`.
-   **CloudFront**: Delivers frontend assets from S3 globally for fast user access.
-   **S3**: Hosts static frontend assets in `webapp` bucket for CloudFront distribution.

## Prerequisites

Some of the features in this sample app require a LocalStack Pro license - make sure your Auth Token is configured in your terminal session.

## Start LocalStack

Start your LocalStack container with the following configuration:

```bash
EXTRA_CORS_ALLOWED_ORIGINS='*' DISABLE_CUSTOM_CORS_APIGATEWAY=1 DISABLE_CUSTOM_CORS_S3=1 localstack start
```

If you run into specific CORS issues, disable it using a [browser extension](https://webextension.org/listing/access-control.html).

## Local Deployment

To deploy the app locally, run the following command:

```bash
bash bin/deploy.sh
```
The output will be:

```bash 
CloudFront URL: https://1e372b81.cloudfront.localhost.localstack.cloud
API Gateway Endpoint: http://localhost:4566/_aws/execute-api/4xu5emxibf/test
```

Navigate to the CloudFront URL to check out the app. The script would also seed some quiz data and user data to make local testing easier.

## Local Testing

To run an automated test suite against the local deployment, run the following command:

```bash
pip3 install -r tests/requirements-dev.txt
pytest tests/test_infra.py
```

The automated tests utilize the AWS SDK for Python (boto3) and the `requests` library to interact with the Quiz App API. They automate the creation of quizzes, submission of answers, and retrieval of scores and leaderboard details to verify the app's functionality in an end-to-end manner.

## Stack Insights

While testing your app infrastructure, you can retrieve detailed API telemetry over [Stack Insights](https://app.localstack.cloud/stacks). This includes:

-   Number of API calls
-   Service invocations
-   User agent (e.g.,  `aws-cli`,  `terraform`)
-   Specific services called during the instance
-   Use the slide toggle to select a time period to view specific API calls

## Resource Browser

You can use Resource Browser to inspect & manage some of the local resources, such as:

* [DynamoDB](https://app.localstack.cloud/inst/default/resources/dynamodb)
* [Lambda](https://app.localstack.cloud/inst/default/resources/lambda/functions) 
* [API Gateway](https://app.localstack.cloud/inst/default/resources/apigateway)

Click on the resources to inspect their configurations and observe how they operate locally with detailed granularity. You can view additional running services on the [Status Page](https://app.localstack.cloud/inst/default/status). With the exception of EventBridge Pipes and STS, resources for all other services are accessible in a unified view.

## Cloud Pods

To avoid deploying from scratch, you can setup the local development environment using Cloud Pods. To setup the entire stack using Cloud Pods, re-start your LocalStack container:

```bash 
localstack restart
```

Run the following command to inject the infrastructure state from Cloud Pods:

```bash 
localstack pod load serverless-quiz-app
```

Make sure your Auth Token is in your terminal session. You can get the link to the live app in the following fashion:

```bash
DISTRIBUTION_ID=$(awslocal cloudfront list-distributions | jq -r '.DistributionList.Items[0].Id')
echo "https://$DISTRIBUTION_ID.cloudfront.localhost.localstack.cloud"
```

Your app is now ready to be tested!

## Extensions

After a quiz response is submitted, a Step Functions state machine triggers SES to send an email if an address is provided. To view the email, you can utilize the [LocalStack MailHog Extension](https://pypi.org/project/localstack-extension-mailhog/). Install the MailHog Extension through the [Extensions Manager](https://app.localstack.cloud/inst/default/extensions/manage) or by using the following command:

```bash 
localstack extensions install localstack-extension-mailhog
```

Deploy the stack using the above script or Cloud Pods and submit a quiz response. Visit [**mailhog.localhost.localstack.cloud:4566**](https://mailhog.localhost.localstack.cloud:4566/) to see an email response with your scores.

Alternatively, you can inspect the SES Developer endpoint for emails in the following manner:

```bash 
curl -s http://localhost.localstack.cloud:4566/_aws/ses
```

## Continuous Integration

For testing the app within the GitHub Actions workflow, you can refer to the provided workflow in [`integration-test.yml`](.github/workflows/integration-test.yml). This workflow utilizes the [`setup-localstack`](https://github.com/localstack/setup-localstack) action to start LocalStack, deploy the stack, execute tests, and perform final verification. Sample runs are available on the [Actions page](https://github.com/localstack-samples/serverless-quiz-app/actions/workflows/integration-test.yml).

## IAM Policy Stream

Visit the [IAM Policy Stream](https://app.localstack.cloud/inst/default/policy-stream) to view the permissions required for each API call. This feature enables you to explore and progressively enhance security as your application develops.

To get started, restart the LocalStack container using the command `localstack restart` and load the Cloud Pod. Then, click on **Enable**.

> Add **SQS** in the **Exclude Services** dropdown. This step filters out background API calls that aren't necessary for the demo.

Engage with the application or run tests to generate a policy stream for various services. During this process, you may notice some **IAM Violations**. These are intentionally included to demonstrate how the IAM Policy Stream can be used to test policies in a secure developer setting, helping to identify and resolve missing policies to ensure everything works in production environments.

## Chaos Engineering

To experiment with Chaos in your developer environment, visit the [Chaos Engineering dashboard](https://app.localstack.cloud/chaos-engineering). Here, you can inject various chaos scenarios, such as rendering the DynamoDB service unavailable in the `us-east-1` region or introducing a 90% occurrence of `ProvisionedThroughputExceededException` errors in your DynamoDB calls to observe how the application handles these disruptions.

The application is designed with a robust architectural pattern: if a new quiz is created during a DynamoDB outage, the response is captured in an SNS topic, forwarded to an SQS queue, and then processed by a Lambda function which continues to attempt processing until the DynamoDB table is available again.

To test this pattern, execute the automated test suite with the following command:

```bash
pytest tests/test_outage.py
``` 

## Ephemeral Instance

To launch a short-lived, encapsulated deployment of the application on a remote LocalStack instance, you can utilize LocalStack Ephemeral Instances. Execute the following command to create an instance, deploy the resources, and retrieve the application URL:

```bash
bash bin/ephemeral.sh
```

This setup process typically takes about 1-2 minutes. Each Ephemeral Instance will remain active for 2 hours. If continuous availability is required for demo purposes, the instance will need to be recreated every 2 hours.

> Alternatively, you can initiate the Ephemeral Instance through the Web App and load the `serverless-quiz-app` Cloud Pod. Note that the frontend of the app depends on local backend APIs (`localhost:4566`) and will not function in this remote setup. Future enhancements are planned to address this limitation by allowing the injection of the Ephemeral Instance URL into resources using an environment variable.

You can utilize GitHub Actions to launch an Ephemeral Instance with your app stack deployed, facilitating Application Previews. The process is outlined in the [`preview.yml`](.github/workflows/preview.yml) file, which employs the [`setup-localstack`](https://github.com/localstack/setup-localstack) GitHub Action. For practical implementation, view a [sample pull request](https://github.com/localstack-samples/serverless-quiz-app/pull/3) that demonstrates how this setup can enhance collaboration and facilitate acceptance testing.

## License

Apache License 2.0
