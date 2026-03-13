# MANUAL SETUP REQUIRED:
# - Upload custom model files to S3 bucket model/ directory
# - Create Lambda function code in lambda/agent_orchestrator/
# - Configure Bedrock model access in AWS account
# - Set up SageMaker model inference code
# - Update agent instruction prompt for specific use cases
# - Configure model endpoint routing logic

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_bedrock as bedrock,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as _lambda
)
from constructs import Construct

class BedrockAgentSagemakerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for agent data and model artifacts
        self.agent_bucket = self._create_agent_bucket()


        # Create SageMaker endpoint for custom model
        self.sagemaker_endpoint = self._create_sagemaker_endpoint()

        # Create Bedrock Agent
        self.bedrock_agent = self._create_bedrock_agent()

        # Create Lambda function for agent orchestration
        self.agent_orchestrator = self._create_agent_orchestrator()

    def _create_agent_bucket(self) -> s3.Bucket:
        """Create S3 bucket for storing agent knowledge base and model artifacts"""
        return s3.Bucket(
            self, "AgentDataBucket",
            bucket_name=f"agent-data-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )


    def _create_sagemaker_endpoint(self) -> sagemaker.CfnEndpoint:
        """Create SageMaker endpoint for custom model hosting"""

        # IAM role for SageMaker
        sagemaker_role = iam.Role(
            self, "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
            ]
        )

        # Grant access to agent bucket
        self.agent_bucket.grant_read_write(sagemaker_role)

        # SageMaker model configuration
        model = sagemaker.CfnModel(
            self, "AgentModel",
            execution_role_arn=sagemaker_role.role_arn,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image="763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:2.0.0-cpu-py38",
                model_data_url=f"s3://{self.agent_bucket.bucket_name}/model/",
                environment={
                    "SAGEMAKER_PROGRAM": "inference.py",
                    "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code",
                    "SAGEMAKER_CONTAINER_LOG_LEVEL": "20",
                    "SAGEMAKER_REGION": cdk.Aws.REGION
                }
            )
        )

        # SageMaker endpoint configuration
        endpoint_config = sagemaker.CfnEndpointConfig(
            self, "AgentEndpointConfig",
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    model_name=model.model_name,
                    variant_name="AllTraffic",
                    initial_instance_count=1,
                    instance_type="ml.m5.large"
                )
            ]
        )

        # SageMaker endpoint
        endpoint = sagemaker.CfnEndpoint(
            self, "AgentEndpoint",
            endpoint_config_name=endpoint_config.endpoint_config_name
        )

        # Add dependency
        endpoint.add_dependency(model)
        endpoint.add_dependency(endpoint_config)

        return endpoint

    def _create_bedrock_agent(self) -> bedrock.CfnAgent:
        """Create Bedrock Agent for AI orchestration"""

        # IAM role for Bedrock Agent
        agent_role = iam.Role(
            self, "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "AgentPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:Retrieve",
                                "bedrock:RetrieveAndGenerate"
                            ],
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetObject", "s3:PutObject"],
                            resources=[f"{self.agent_bucket.bucket_arn}/*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["sagemaker:InvokeEndpoint"],
                            resources=[self.sagemaker_endpoint.attr_endpoint_arn]
                        )
                    ]
                )
            }
        )

        # Bedrock Agent
        agent = bedrock.CfnAgent(
            self, "AgenticWorkflowAgent",
            agent_name="agentic-workflow-agent",
            instruction="You are an AI agent that orchestrates complex workflows by coordinating multiple AI models and services. You can analyze tasks, route them to appropriate models, and aggregate results.",
            foundation_model="anthropic.claude-3-sonnet-20240229-v1:0",
            role_arn=agent_role.role_arn,
            idle_time_ttl_ttl_seconds=300,
            customer_encryption_key_arn=None
        )

        return agent

    def _create_agent_orchestrator(self) -> _lambda.Function:
        """Lambda function to orchestrate Bedrock Agent and SageMaker interactions"""

        # IAM role for Lambda
        lambda_role = iam.Role(
            self, "AgentOrchestratorRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Grant permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeAgent"],
                resources=[self.bedrock_agent.attr_agent_arn]
            )
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sagemaker:InvokeEndpoint"],
                resources=[self.sagemaker_endpoint.attr_endpoint_arn]
            )
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject", "s3:PutObject"],
                resources=[f"{self.agent_bucket.bucket_arn}/*"]
            )
        )

        # Lambda function
        function = _lambda.Function(
            self, "AgentOrchestratorLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="agent_orchestrator.handler",
            code=_lambda.Code.from_asset("lambda/agent_orchestrator"),
            timeout=cdk.Duration.minutes(15),
            memory_size=1024,
            role=lambda_role,
            environment={
                "BEDROCK_AGENT_ID": self.bedrock_agent.attr_agent_id,
                "SAGEMAKER_ENDPOINT_NAME": self.sagemaker_endpoint.attr_endpoint_name,
                "AGENT_BUCKET_NAME": self.agent_bucket.bucket_name,
                "AWS_REGION": cdk.Aws.REGION
            }
        )

        return function