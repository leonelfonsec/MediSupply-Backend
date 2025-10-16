#!/usr/bin/env bash
set -euo pipefail

# Crear colas
QUEUE_URL=$(awslocal sqs create-queue \
    --queue-name orders.fifo \
    --attributes FifoQueue=true,ContentBasedDeduplication=true \
    --query QueueUrl --output text)

DLQ_URL=$(awslocal sqs create-queue \
    --queue-name orders-dlq.fifo \
    --attributes FifoQueue=true \
    --query QueueUrl --output text)

# Obtener ARN de la DLQ
DLQ_ARN=$(awslocal sqs get-queue-attributes \
    --queue-url "$DLQ_URL" \
    --attribute-names QueueArn \
    --query Attributes.QueueArn --output text)

# Crear archivo temporal con los atributos (evita problemas de quoting)
ATTR_FILE="/tmp/queue-attrs.json"
cat > "$ATTR_FILE" << EOF
{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"$DLQ_ARN\",\"maxReceiveCount\":\"5\"}"
}
EOF

# Aplicar atributos desde archivo
awslocal sqs set-queue-attributes \
    --queue-url "$QUEUE_URL" \
    --attributes "file://$ATTR_FILE"

echo "SQS ready"