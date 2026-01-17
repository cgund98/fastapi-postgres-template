#!/bin/bash
# Setup script for LocalStack SNS topics and SQS queues

set -e

ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:4566}"
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

# Create SQS queues for each event type
echo "Creating SQS queues..."

# User events
echo "Creating user-created queue..."
USER_CREATED_QUEUE=$(aws --endpoint-url=$ENDPOINT_URL sqs create-queue \
  --queue-name user-created \
  --region $REGION \
  --output text \
  --query 'QueueUrl' 2>&1) || {
  echo "Error creating user-created queue:" >&2
  echo "$USER_CREATED_QUEUE" >&2
  exit 1
}
echo "Created queue: $USER_CREATED_QUEUE"

echo "Creating user-updated queue..."
USER_UPDATED_QUEUE=$(aws --endpoint-url=$ENDPOINT_URL sqs create-queue \
  --queue-name user-updated \
  --region $REGION \
  --output text \
  --query 'QueueUrl' 2>&1) || {
  echo "Error creating user-updated queue:" >&2
  echo "$USER_UPDATED_QUEUE" >&2
  exit 1
}
echo "Created queue: $USER_UPDATED_QUEUE"

# Invoice events
echo "Creating invoice-created queue..."
INVOICE_CREATED_QUEUE=$(aws --endpoint-url=$ENDPOINT_URL sqs create-queue \
  --queue-name invoice-created \
  --region $REGION \
  --output text \
  --query 'QueueUrl' 2>&1) || {
  echo "Error creating invoice-created queue:" >&2
  echo "$INVOICE_CREATED_QUEUE" >&2
  exit 1
}
echo "Created queue: $INVOICE_CREATED_QUEUE"

echo "Creating invoice-payment-requested queue..."
INVOICE_PAYMENT_REQUESTED_QUEUE=$(aws --endpoint-url=$ENDPOINT_URL sqs create-queue \
  --queue-name invoice-payment-requested \
  --region $REGION \
  --output text \
  --query 'QueueUrl' 2>&1) || {
  echo "Error creating invoice-payment-requested queue:" >&2
  echo "$INVOICE_PAYMENT_REQUESTED_QUEUE" >&2
  exit 1
}
echo "Created queue: $INVOICE_PAYMENT_REQUESTED_QUEUE"

echo "Creating invoice-paid queue..."
INVOICE_PAID_QUEUE=$(aws --endpoint-url=$ENDPOINT_URL sqs create-queue \
  --queue-name invoice-paid \
  --region $REGION \
  --output text \
  --query 'QueueUrl' 2>&1) || {
  echo "Error creating invoice-paid queue:" >&2
  echo "$INVOICE_PAID_QUEUE" >&2
  exit 1
}
echo "Created queue: $INVOICE_PAID_QUEUE"

# Get queue ARNs for subscription
echo "Getting queue ARNs..."

USER_CREATED_QUEUE_ARN=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
  --queue-url "$USER_CREATED_QUEUE" \
  --attribute-names QueueArn \
  --region $REGION \
  --output text \
  --query 'Attributes.QueueArn' 2>&1) || {
  echo "Error getting user-created queue ARN:" >&2
  echo "$USER_CREATED_QUEUE_ARN" >&2
  exit 1
}

USER_UPDATED_QUEUE_ARN=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
  --queue-url "$USER_UPDATED_QUEUE" \
  --attribute-names QueueArn \
  --region $REGION \
  --output text \
  --query 'Attributes.QueueArn' 2>&1) || {
  echo "Error getting user-updated queue ARN:" >&2
  echo "$USER_UPDATED_QUEUE_ARN" >&2
  exit 1
}

INVOICE_CREATED_QUEUE_ARN=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
  --queue-url "$INVOICE_CREATED_QUEUE" \
  --attribute-names QueueArn \
  --region $REGION \
  --output text \
  --query 'Attributes.QueueArn' 2>&1) || {
  echo "Error getting invoice-created queue ARN:" >&2
  echo "$INVOICE_CREATED_QUEUE_ARN" >&2
  exit 1
}

INVOICE_PAYMENT_REQUESTED_QUEUE_ARN=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
  --queue-url "$INVOICE_PAYMENT_REQUESTED_QUEUE" \
  --attribute-names QueueArn \
  --region $REGION \
  --output text \
  --query 'Attributes.QueueArn' 2>&1) || {
  echo "Error getting invoice-payment-requested queue ARN:" >&2
  echo "$INVOICE_PAYMENT_REQUESTED_QUEUE_ARN" >&2
  exit 1
}

INVOICE_PAID_QUEUE_ARN=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
  --queue-url "$INVOICE_PAID_QUEUE" \
  --attribute-names QueueArn \
  --region $REGION \
  --output text \
  --query 'Attributes.QueueArn' 2>&1) || {
  echo "Error getting invoice-paid queue ARN:" >&2
  echo "$INVOICE_PAID_QUEUE_ARN" >&2
  exit 1
}

# Subscribe queues to SNS topic with filter policies
echo "Subscribing queues to SNS topic..."

echo "Subscribing user-created queue..."
USER_CREATED_SUBSCRIPTION_ARN=$(aws --endpoint-url=$ENDPOINT_URL sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$USER_CREATED_QUEUE_ARN" \
  --attributes '{"FilterPolicy":"{\"event_type\":[\"user.created\"]}","RawMessageDelivery":"true"}' \
  --region $REGION \
  --output text \
  --query 'SubscriptionArn' 2>&1) || {
  echo "Error subscribing user-created queue:" >&2
  echo "$USER_CREATED_SUBSCRIPTION_ARN" >&2
  exit 1
}
echo "Subscribed user-created queue to topic with filter policy and raw message delivery"

echo "Subscribing user-updated queue..."
USER_UPDATED_SUBSCRIPTION_ARN=$(aws --endpoint-url=$ENDPOINT_URL sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$USER_UPDATED_QUEUE_ARN" \
  --attributes '{"FilterPolicy":"{\"event_type\":[\"user.updated\"]}","RawMessageDelivery":"true"}' \
  --region $REGION \
  --output text \
  --query 'SubscriptionArn' 2>&1) || {
  echo "Error subscribing user-updated queue:" >&2
  echo "$USER_UPDATED_SUBSCRIPTION_ARN" >&2
  exit 1
}
echo "Subscribed user-updated queue to topic with filter policy and raw message delivery"

echo "Subscribing invoice-created queue..."
INVOICE_CREATED_SUBSCRIPTION_ARN=$(aws --endpoint-url=$ENDPOINT_URL sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$INVOICE_CREATED_QUEUE_ARN" \
  --attributes '{"FilterPolicy":"{\"event_type\":[\"invoice.created\"]}","RawMessageDelivery":"true"}' \
  --region $REGION \
  --output text \
  --query 'SubscriptionArn' 2>&1) || {
  echo "Error subscribing invoice-created queue:" >&2
  echo "$INVOICE_CREATED_SUBSCRIPTION_ARN" >&2
  exit 1
}
echo "Subscribed invoice-created queue to topic with filter policy and raw message delivery"

echo "Subscribing invoice-payment-requested queue..."
INVOICE_PAYMENT_REQUESTED_SUBSCRIPTION_ARN=$(aws --endpoint-url=$ENDPOINT_URL sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$INVOICE_PAYMENT_REQUESTED_QUEUE_ARN" \
  --attributes '{"FilterPolicy":"{\"event_type\":[\"invoice.payment_requested\"]}","RawMessageDelivery":"true"}' \
  --region $REGION \
  --output text \
  --query 'SubscriptionArn' 2>&1) || {
  echo "Error subscribing invoice-payment-requested queue:" >&2
  echo "$INVOICE_PAYMENT_REQUESTED_SUBSCRIPTION_ARN" >&2
  exit 1
}
echo "Subscribed invoice-payment-requested queue to topic with filter policy and raw message delivery"

echo "Subscribing invoice-paid queue..."
INVOICE_PAID_SUBSCRIPTION_ARN=$(aws --endpoint-url=$ENDPOINT_URL sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$INVOICE_PAID_QUEUE_ARN" \
  --attributes '{"FilterPolicy":"{\"event_type\":[\"invoice.paid\"]}","RawMessageDelivery":"true"}' \
  --region $REGION \
  --output text \
  --query 'SubscriptionArn' 2>&1) || {
  echo "Error subscribing invoice-paid queue:" >&2
  echo "$INVOICE_PAID_SUBSCRIPTION_ARN" >&2
  exit 1
}
echo "Subscribed invoice-paid queue to topic with filter policy and raw message delivery"

echo ""
echo "Setup complete!"
echo ""
echo "AWS_ENDPOINT_URL=$ENDPOINT_URL"
echo "AWS_REGION=$REGION"
echo "DEFAULT_EVENT_TOPIC_ARN=$TOPIC_ARN"
echo "EVENT_QUEUE_URL_USER_CREATED=$USER_CREATED_QUEUE"
echo "EVENT_QUEUE_URL_USER_UPDATED=$USER_UPDATED_QUEUE"
echo "EVENT_QUEUE_URL_INVOICE_CREATED=$INVOICE_CREATED_QUEUE"
echo "EVENT_QUEUE_URL_INVOICE_PAYMENT_REQUESTED=$INVOICE_PAYMENT_REQUESTED_QUEUE"
echo "EVENT_QUEUE_URL_INVOICE_PAID=$INVOICE_PAID_QUEUE"
