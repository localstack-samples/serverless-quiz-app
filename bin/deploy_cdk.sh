#!/usr/bin/env bash

set -euo pipefail

AWS_CMD=${AWS_CMD:-aws}
CDK_CMD=${CDK_CMD:-cdk}

# deploy bulk of the application
(cd cdk
npm run cdk -- deploy --require-approval never QuizAppStack
)

# get the backend API url
API_URL=$($AWS_CMD cloudformation describe-stacks --stack-name QuizAppStack --query Stacks[0].Outputs[0].OutputValue --output text)
echo "Backend API URL: $API_URL"

# build the frontend code
(cd frontend
echo "REACT_APP_API_ENDPOINT=$API_URL" > .env.local
npx react-scripts build
)

# deploy the frontend stack
(cd cdk
npm run ${CDK_CMD} -- deploy --require-approval never FrontendStack
)
