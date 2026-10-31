# Cloud deployment

This branch contains two deployment paths. Local development continues to use
the existing `.env` access-key configuration. ECS production uses an ECS task
role and does not store AWS access keys in the container.

## Development S3 bucket

Create only the development bucket:

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/s3-dev.yaml \
  --stack-name mavchat-s3-dev \
  --parameter-overrides AppOrigin=http://localhost:8000
```

The development template also creates a narrowly scoped IAM user and access
key. Copy the stack outputs into local `.env`:

```env
S3_ENDPOINT_URL=
S3_REGION=<Region output>
S3_BUCKET_NAME=<BucketName output>
S3_ACCESS_KEY_ID=<AccessKeyId output>
S3_SECRET_ACCESS_KEY=<SecretAccessKey output>
```

The secret access key is only returned when the stack creates the key. Treat it
as a development secret and do not commit it.

## Production prerequisites

- VPC with at least two public and two private subnets.
- NAT access or VPC endpoints from private subnets to ECR, CloudWatch Logs, and S3.
- ECR image URI for the application container.
- ACM certificate for the production domain in the same Region as the ALB.
- Production database connection string and strong session secret.
- Database network access configured for ECS.

## Production ECS and S3 deployment

The production template creates the ECS Fargate cluster and service, HTTPS
Application Load Balancer, security groups, task roles, CloudWatch log group,
private S3 bucket, and S3 CORS rules.

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/production.yaml \
  --stack-name mavchat-production \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    VpcId=vpc-xxxxxxxx \
    PublicSubnetIds=subnet-public-a,subnet-public-b \
    PrivateSubnetIds=subnet-private-a,subnet-private-b \
    ContainerImage=123456789012.dkr.ecr.us-east-1.amazonaws.com/mavchat:latest \
    CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxx \
    AppOrigin=https://chat.example.com \
    DatabaseUrl='your-production-database-url' \
    SessionSecret='your-production-session-secret'
```

Point the production domain to the stack's `LoadBalancerDnsName` output. Do not
point the domain directly at an ECS task IP because task IPs can change.

The ECS task role grants only `s3:PutObject` and `s3:GetObject` under
`chat-attachments/`. The browser receives short-lived presigned URLs from the
authenticated app and never receives AWS credentials.

For production hardening, move `DATABASE_URL` and `SESSION_SECRET` from
CloudFormation parameters into AWS Secrets Manager and reference them through
the ECS task definition's `Secrets` field.
