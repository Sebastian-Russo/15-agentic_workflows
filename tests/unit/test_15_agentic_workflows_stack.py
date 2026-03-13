import aws_cdk as core
import aws_cdk.assertions as assertions

from 15_agentic_workflows.15_agentic_workflows_stack import 15AgenticWorkflowsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in 15_agentic_workflows/15_agentic_workflows_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = 15AgenticWorkflowsStack(app, "15-agentic-workflows")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
