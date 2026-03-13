#!/usr/bin/env python3
import os

import aws_cdk as cdk

from src.step_functions_stack import StepFunctionsStack
from src.strands_stack import StrandsStack
from src.bedrock_agent_sagemaker_stack import BedrockAgentSagemakerStack


app = cdk.App()

# Step Functions Stack
step_functions_stack = StepFunctionsStack(app, "StepFunctionsStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

# Strands Stack
strands_stack = StrandsStack(app, "StrandsStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

# Bedrock Agent & SageMaker Stack
bedrock_agent_stack = BedrockAgentSagemakerStack(app, "BedrockAgentSagemakerStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

app.synth()
