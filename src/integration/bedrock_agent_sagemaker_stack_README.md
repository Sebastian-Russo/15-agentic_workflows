# Bedrock Agent & SageMaker Stack

## Resources Created

- **S3 Bucket**: `AgentDataBucket`
  - Stores agent knowledge base and model artifacts
  - S3-managed encryption, block public access
  - Destroy removal policy for development

- **SageMaker Endpoint**: `AgentEndpoint`
  - Hosts custom models using HuggingFace PyTorch container
  - ml.m5.large instance type
  - Model data from S3 bucket

- **Bedrock Agent**: `AgenticWorkflowAgent`
  - Uses Claude 3 Sonnet foundation model
  - Orchestrates complex AI workflows
  - 5-minute idle timeout

- **Lambda Function**: `AgentOrchestratorLambda`
  - Coordinates Bedrock Agent and SageMaker interactions
  - 15-minute timeout, 1024MB memory
  - Non-VPC isolated for simplicity

## Manual Setup Required

- Upload custom model files to S3 bucket `model/` directory
- Create Lambda function code in `lambda/agent_orchestrator/`
- Configure Bedrock model access in AWS account
- Set up SageMaker model inference code
- Update agent instruction prompt for specific use cases
- Configure model endpoint routing logic
