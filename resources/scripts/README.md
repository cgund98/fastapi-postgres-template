# LocalStack Setup

This directory contains scripts for setting up LocalStack resources for local development.

## Prerequisites

1. Docker and Docker Compose installed
2. AWS CLI installed (`aws --version`)
3. LocalStack running (`docker-compose up -d localstack`)

## Setup

1. Start LocalStack:
   ```bash
   docker-compose up -d localstack
   ```

2. Wait for LocalStack to be healthy (check with `docker-compose ps`)

3. Run the setup script:
   ```bash
   ./resources/scripts/setup_localstack.sh
   ```

   The script automatically sets dummy AWS credentials (test/test) for LocalStack.
   You can override these with environment variables if needed:
   ```bash
   AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_ENDPOINT_URL=http://localhost:4566 ./resources/scripts/setup_localstack.sh
   ```

4. Copy the environment variables from the script output to your `.env` file

## Environment Variables

### Script Input Variables

The script accepts the following environment variables (all optional with defaults):

- `AWS_ENDPOINT_URL` (default: `http://localhost:4566`) - LocalStack endpoint
- `AWS_REGION` (default: `us-east-1`) - AWS region
- `AWS_ACCESS_KEY_ID` (default: `test`) - AWS access key (dummy value for LocalStack)
- `AWS_SECRET_ACCESS_KEY` (default: `test`) - AWS secret key (dummy value for LocalStack)

### Script Output Variables

The setup script will output the following environment variables that you need to add to your `.env` file:

- `AWS_ENDPOINT_URL=http://localhost:4566`
- `AWS_REGION=us-east-1`
- `DEFAULT_EVENT_TOPIC_ARN=<topic-arn>`
- `EVENT_QUEUE_URL_USER_CREATED=<queue-url>`
- `EVENT_QUEUE_URL_USER_UPDATED=<queue-url>`
- `EVENT_QUEUE_URL_INVOICE_CREATED=<queue-url>`
- `EVENT_QUEUE_URL_INVOICE_PAYMENT_REQUESTED=<queue-url>`
- `EVENT_QUEUE_URL_INVOICE_PAID=<queue-url>`

## Architecture

The setup script creates:
- 1 SNS topic (`events-topic`) for publishing events
- 5 SQS queues (one for each event type)
- Subscriptions linking queues to the topic with filter policies based on `event_type`

Events published to the SNS topic will be automatically routed to the appropriate queue based on the `event_type` message attribute.

