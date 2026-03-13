# MANUAL SETUP REQUIRED:
# - Create Lambda function code in lambda/strand_processor/, lambda/strand_coordinator/, lambda/strand_aggregator/
# - Implement strand-specific processing logic for different data types
# - Configure DynamoDB tables for strand state management
# - Set up SNS topics for strand event notifications
# - Implement strand lifecycle management and cleanup
# - Add monitoring and alerting for strand failures

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets
)
from constructs import Construct

class StrandsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB tables for strand state
        self.strand_state_table = self._create_strand_state_table()
        self.strand_metadata_table = self._create_strand_metadata_table()

        # Create SNS topics for strand events
        self.strand_events_topic = self._create_strand_events_topic()

        # Create SQS queues for strand processing
        self.strand_queue = self._create_strand_queue()

        # Create Lambda functions for strand processing
        self.strand_processor = self._create_strand_processor()
        self.strand_coordinator = self._create_strand_coordinator()
        self.strand_aggregator = self._create_strand_aggregator()

        # Create EventBridge rules for strand orchestration
        self.strand_orchestrator = self._create_strand_orchestrator()

        # Grant permissions
        self._grant_permissions()

    def _create_strand_state_table(self) -> dynamodb.Table:
        """Create DynamoDB table for tracking strand execution state"""
        return dynamodb.Table(
            self, "StrandStateTable",
            partition_key=dynamodb.Attribute(name="strand_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="execution_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
            stream_specification=dynamodb.StreamSpecification(
                stream_view_type=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
            )
        )

    def _create_strand_metadata_table(self) -> dynamodb.Table:
        """Create DynamoDB table for strand metadata and configuration"""
        return dynamodb.Table(
            self, "StrandMetadataTable",
            partition_key=dynamodb.Attribute(name="strand_type", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="strand_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

    def _create_strand_events_topic(self) -> sns.Topic:
        """Create SNS topic for strand event notifications"""
        return sns.Topic(
            self, "StrandEventsTopic",
            display_name="Strand Events",
            topic_name="strand-events"
        )

    def _create_strand_queue(self) -> sqs.Queue:
        """Create SQS queue for strand processing tasks"""
        return sqs.Queue(
            self, "StrandQueue",
            queue_name="strand-processing-queue",
            visibility_timeout=cdk.Duration.minutes(15),
            retention_period=cdk.Duration.days(14),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=sqs.Queue(self, "StrandDLQ", queue_name="strand-dlq")
            )
        )

    def _create_strand_processor(self) -> _lambda.Function:
        """Lambda function for processing individual strands"""
        return _lambda.Function(
            self, "StrandProcessor",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="strand_processor.handler",
            code=_lambda.Code.from_asset("lambda/strand_processor"),
            timeout=cdk.Duration.minutes(10),
            memory_size=512,
            environment={
                "STRAND_STATE_TABLE": self.strand_state_table.table_name,
                "STRAND_METADATA_TABLE": self.strand_metadata_table.table_name,
                "STRAND_EVENTS_TOPIC_ARN": self.strand_events_topic.topic_arn,
                "STRAND_QUEUE_URL": self.strand_queue.queue_url
            }
        )

    def _create_strand_coordinator(self) -> _lambda.Function:
        """Lambda function for coordinating multiple strands"""
        return _lambda.Function(
            self, "StrandCoordinator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="strand_coordinator.handler",
            code=_lambda.Code.from_asset("lambda/strand_coordinator"),
            timeout=cdk.Duration.minutes(15),
            memory_size=1024,
            environment={
                "STRAND_STATE_TABLE": self.strand_state_table.table_name,
                "STRAND_METADATA_TABLE": self.strand_metadata_table.table_name,
                "STRAND_EVENTS_TOPIC_ARN": self.strand_events_topic.topic_arn,
                "STRAND_QUEUE_URL": self.strand_queue.queue_url
            }
        )

    def _create_strand_aggregator(self) -> _lambda.Function:
        """Lambda function for aggregating results from multiple strands"""
        return _lambda.Function(
            self, "StrandAggregator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="strand_aggregator.handler",
            code=_lambda.Code.from_asset("lambda/strand_aggregator"),
            timeout=cdk.Duration.minutes(20),
            memory_size=1024,
            environment={
                "STRAND_STATE_TABLE": self.strand_state_table.table_name,
                "STRAND_METADATA_TABLE": self.strand_metadata_table.table_name,
                "STRAND_EVENTS_TOPIC_ARN": self.strand_events_topic.topic_arn
            }
        )

    def _create_strand_orchestrator(self) -> events.Rule:
        """Create EventBridge rule for strand orchestration"""
        rule = events.Rule(
            self, "StrandOrchestratorRule",
            description="Orchestrate strand processing workflows",
            event_pattern=events.EventPattern(
                source=["aws.dynamodb"],
                detail_type=["DynamoDB Streams Record"],
                detail={
                    "eventSourceARN": [self.strand_state_table.table_stream_arn]
                }
            )
        )

        # Add targets for different strand events
        rule.add_target(targets.LambdaFunction(self.strand_processor))
        rule.add_target(targets.LambdaFunction(self.strand_coordinator))

        return rule

    def _grant_permissions(self):
        """Grant necessary permissions to Lambda functions"""
        # Grant DynamoDB permissions
        self.strand_state_table.grant_read_write_data(self.strand_processor)
        self.strand_state_table.grant_read_write_data(self.strand_coordinator)
        self.strand_state_table.grant_read_write_data(self.strand_aggregator)

        self.strand_metadata_table.grant_read_write_data(self.strand_processor)
        self.strand_metadata_table.grant_read_write_data(self.strand_coordinator)
        self.strand_metadata_table.grant_read_write_data(self.strand_aggregator)

        # Grant SNS permissions
        self.strand_events_topic.grant_publish(self.strand_processor)
        self.strand_events_topic.grant_publish(self.strand_coordinator)
        self.strand_events_topic.grant_publish(self.strand_aggregator)

        # Grant SQS permissions
        self.strand_queue.grant_send_messages(self.strand_processor)
        self.strand_queue.grant_consume_messages(self.strand_coordinator)