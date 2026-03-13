# Strands Stack

## Resources Created

- **2 DynamoDB Tables**:
  - `StrandStateTable`: Tracks strand execution state with streams
  - `StrandMetadataTable`: Stores strand metadata and configuration

- **1 SNS Topic**: `StrandEventsTopic`
  - Event notifications for strand lifecycle events

- **1 SQS Queue**: `StrandQueue`
  - Processing queue with DLQ for failed strands
  - 15-minute visibility timeout, 14-day retention

- **3 Lambda Functions**:
  - `StrandProcessor`: Processes individual strands (10min timeout, 512MB memory)
  - `StrandCoordinator`: Coordinates multiple strands (15min timeout, 1024MB memory)
  - `StrandAggregator`: Aggregates results from multiple strands (20min timeout, 1024MB memory)

- **1 EventBridge Rule**: `StrandOrchestratorRule`
  - Triggers Lambda functions based on DynamoDB stream events
  - Orchestrates strand processing workflows

## Manual Setup Required

- Create Lambda function code in lambda/strand_processor/, lambda/strand_coordinator/, lambda/strand_aggregator/
- Implement strand-specific processing logic for different data types
- Configure DynamoDB tables for strand state management
- Set up SNS topics for strand event notifications
- Implement strand lifecycle management and cleanup
- Add monitoring and alerting for strand failures
