#!/bin/bash
# Setup script for LocalStack SNS topics and SQS queues

set -e

ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localstack:4566}"
REGION="${AWS_REGION:-us-east-1}"

# Override AWS credentials for LocalStack (LocalStack doesn't validate these)
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
export AWS_DEFAULT_REGION="${REGION}"

echo "Setting up LocalStack resources..."
echo "Endpoint: $ENDPOINT_URL"
echo "Region: $REGION"
echo ""

# Create SNS topic for events
echo "Creating SNS topic..."
TOPIC_ARN=$(aws --endpoint-url=$ENDPOINT_URL sns create-topic \
  --name events-topic \
  --region $REGION \
  --output text \
  --query 'TopicArn' 2>&1) || {
  echo "Error creating SNS topic:" >&2
  echo "$TOPIC_ARN" >&2
  exit 1
}

if [ -z "$TOPIC_ARN" ] || [[ ! "$TOPIC_ARN" =~ ^arn: ]]; then
  echo "Error: Failed to create SNS topic. Got: $TOPIC_ARN" >&2
  exit 1
fi

echo "Created SNS topic: $TOPIC_ARN"

# Create a single SQS queue for all events
echo "Creating events queue..."
EVENTS_QUEUE=$(aws --endpoint-url=$ENDPOINT_URL sqs create-queue \
  --queue-name events \
  --region $REGION \
  --output text \
  --query 'QueueUrl' 2>&1) || {
  echo "Error creating events queue:" >&2
  echo "$EVENTS_QUEUE" >&2
  exit 1
}
echo "Created queue: $EVENTS_QUEUE"

# Get queue ARN for subscription
echo "Getting queue ARN..."
EVENTS_QUEUE_ARN=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
  --queue-url "$EVENTS_QUEUE" \
  --attribute-names QueueArn \
  --region $REGION \
  --output text \
  --query 'Attributes.QueueArn' 2>&1) || {
  echo "Error getting events queue ARN:" >&2
  echo "$EVENTS_QUEUE_ARN" >&2
  exit 1
}

# Subscribe queue to SNS topic with filter policy for all known event types
echo "Subscribing events queue to SNS topic..."
SUBSCRIPTION_ARN=$(aws --endpoint-url=$ENDPOINT_URL sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$EVENTS_QUEUE_ARN" \
  --attributes '{"FilterPolicy":"{\"event_type\":[\"user.v1.created\",\"user.v1.updated\",\"user.v1.deleted\",\"invoice.v1.created\",\"invoice.v1.payment_requested\",\"invoice.v1.paid\"]}","RawMessageDelivery":"true"}' \
  --region $REGION \
  --output text \
  --query 'SubscriptionArn' 2>&1) || {
  echo "Error subscribing events queue:" >&2
  echo "$SUBSCRIPTION_ARN" >&2
  exit 1
}
echo "Subscribed events queue to topic with filter policy and raw message delivery"

echo ""
echo "Setup complete!"
echo ""
echo "EVENT_TOPIC_ARN=$TOPIC_ARN"
echo "EVENT_QUEUE_URL=$EVENTS_QUEUE"
