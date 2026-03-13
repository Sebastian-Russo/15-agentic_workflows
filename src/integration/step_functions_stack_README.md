# Step Functions Stack

## Resources Created

- **3 Lambda Functions**:
  - `AgentsOrchestrator`: Coordinates multiple AI agents (15min timeout, 1024MB memory)
  - `TaskRouter`: Routes tasks to appropriate agents (5min timeout, 512MB memory)
  - `ResultAggregator`: Aggregates results from multiple agents (10min timeout, 512MB memory)

- **1 State Machine**: `AgenticWorkflowStateMachine`
  - Coordinates workflow with choice-based routing
  - 1-hour timeout
  - Flow: Orchestrate → Route → (Complex tasks → Aggregate) or (Simple tasks → Complete)

## Manual Setup Required

- Create Lambda function code in `lambda/agents_orchestrator/`, `lambda/task_router/`, and `lambda/result_aggregator/`
- Implement task routing logic in the choice state
- Configure environment variables for agent endpoints
- Set up CloudWatch logging and monitoring
