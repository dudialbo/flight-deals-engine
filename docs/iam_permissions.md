# IAM Permissions

This document outlines the AWS IAM permissions required for the Flight Deals Engine Lambda function.

## Execution Role Policy

The Lambda execution role must allow the following actions:

### Logging (CloudWatch Logs)
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

### Storage (DynamoDB)
- `dynamodb:PutItem`
- `dynamodb:BatchWriteItem`
- `dynamodb:UpdateItem`
- `dynamodb:Query` (for hot deals scoring logic if needed)

### Secrets Management (SSM Parameter Store / Secrets Manager)
- `ssm:GetParameter`
- `ssm:GetParameters`
- `kms:Decrypt` (if parameters are encrypted)

### VPC Access (Optional)
If the internal search backend is within a VPC:
- `ec2:CreateNetworkInterface`
- `ec2:DescribeNetworkInterfaces`
- `ec2:DeleteNetworkInterface`

## Minimal Policy Example

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:BatchWriteItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/FlightDeals"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/flight-deals-engine/*"
        }
    ]
}
```
