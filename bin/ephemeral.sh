#!/bin/bash

if [ -z "$LOCALSTACK_API_KEY" ]; then
  echo "Error: LOCALSTACK_API_KEY environment variable is not set."
  exit 1
fi

INSTANCE_NAME="instance-$(openssl rand -hex 4)"
echo "Creating ephemeral instance with name: $INSTANCE_NAME"

ENV_VARS_JSON=$(cat <<EOF
{
  "LAMBDA_KEEPALIVE_MS": "7200000",
  "EXTENSION_AUTO_INSTALL": "localstack-extension-mailhog"
}
EOF
)

CREATE_RESPONSE=$(curl -s -X POST https://api.localstack.cloud/v1/compute/instances \
  -H "Content-Type: application/json" \
  -H "ls-api-key: $LOCALSTACK_API_KEY" \
  -d '{
        "instance_name": "'"$INSTANCE_NAME"'",
        "lifetime": 120,
        "env_vars": '"$ENV_VARS_JSON"'
      }')

if echo "$CREATE_RESPONSE" | grep -q '"endpoint_url"'; then
  echo "Ephemeral instance created successfully."
else
  echo "Error creating ephemeral instance:"
  echo "$CREATE_RESPONSE"
  exit 1
fi

ENDPOINT_URL=$(echo "$CREATE_RESPONSE" | jq -r '.endpoint_url')

export AWS_ENDPOINT_URL="$ENDPOINT_URL"
export ENDPOINT_URL="$ENDPOINT_URL"

echo "Deploying resources..."
bash bin/deploy.sh > /dev/null 2>&1
bash bin/seed.sh > /dev/null 2>&1
echo "Deployment completed."

DISTRIBUTION_ID=$(awslocal cloudfront list-distributions --endpoint-url="$ENDPOINT_URL" | jq -r '.DistributionList.Items[0].Id')

if [ -z "$DISTRIBUTION_ID" ] || [ "$DISTRIBUTION_ID" = "null" ]; then
  echo "Error retrieving CloudFront distribution ID."
  exit 1
fi

echo "Link to the ephemeral instance CloudFront distribution:"
echo "$ENDPOINT_URL/cloudfront/$DISTRIBUTION_ID/"
