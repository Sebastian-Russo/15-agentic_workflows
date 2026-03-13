# MANUAL SETUP REQUIRED:
# - Create Lambda function code in lambda/agents_orchestrator/, lambda/task_router/, lambda/result_aggregator/
# - Implement task routing logic in choice state
# - Configure environment variables for agent endpoints
# - Set up CloudWatch logging and monitoring

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_lambda as _lambda
)
from constructs import Construct

class StepFunctionsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Define Lambda functions for the workflow
        self.agents_orchestrator = self._create_agents_orchestrator()
        self.task_router = self._create_task_router()
        self.result_aggregator = self._create_result_aggregator()

        # Define the Step Functions workflow
        self.workflow = self._create_workflow()

    def _create_agents_orchestrator(self) -> _lambda.Function:
        """Lambda function to orchestrate multiple AI agents"""
        return _lambda.Function(
            self, "AgentsOrchestrator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="agents_orchestrator.handler",
            code=_lambda.Code.from_asset("lambda/agents_orchestrator"),
            timeout=cdk.Duration.minutes(15),
            memory_size=1024,
            environment={
                "BEDROCK_REGION": self.region
            }
        )

    def _create_task_router(self) -> _lambda.Function:
        """Lambda function to route tasks to appropriate agents"""
        return _lambda.Function(
            self, "TaskRouter",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="task_router.handler",
            code=_lambda.Code.from_asset("lambda/task_router"),
            timeout=cdk.Duration.minutes(5),
            memory_size=512
        )

    def _create_result_aggregator(self) -> _lambda.Function:
        """Lambda function to aggregate results from multiple agents"""
        return _lambda.Function(
            self, "ResultAggregator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="result_aggregator.handler",
            code=_lambda.Code.from_asset("lambda/result_aggregator"),
            timeout=cdk.Duration.minutes(10),
            memory_size=512
        )

    def _create_workflow(self) -> sfn.StateMachine:
        """Create the main Step Functions workflow"""

        # Define tasks
        orchestrate_agents = tasks.LambdaInvoke(
            self, "OrchestrateAgents",
            lambda_function=self.agents_orchestrator,
            output_path="$.Payload"
        )

        route_tasks = tasks.LambdaInvoke(
            self, "RouteTasks",
            lambda_function=self.task_router,
            output_path="$.Payload"
        )

        aggregate_results = tasks.LambdaInvoke(
            self, "AggregateResults",
            lambda_function=self.result_aggregator,
            output_path="$.Payload"
        )

        # Define choice state for routing
        task_choice = sfn.Choice(self, "TaskTypeChoice")

        # Build the workflow
        definition = (
            orchestrate_agents
            .next(route_tasks)
            .next(task_choice
                .when(sfn.Condition.string_equals("$.task_type", "complex"), aggregate_results)
                .otherwise(sfn.Succeed(self, "SimpleTaskComplete"))
            )
        )

        return sfn.StateMachine(
            self, "AgenticWorkflowStateMachine",
            definition=definition,
            timeout=cdk.Duration.hours(1),
            comment="State machine for coordinating multiple AI agents"
        )