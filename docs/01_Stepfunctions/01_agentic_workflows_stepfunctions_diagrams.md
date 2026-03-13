# Agentic Workflows with Step Functions — Flow Diagrams

## Module Progression

```mermaid
graph LR
    M1[Module 1<br>Tool Use Concepts] --> M2[Module 2<br>Code-Based Agent<br>Social Media Agent]
    M2 --> M3[Module 3<br>Step Functions Basics<br>Converse API]
    M3 --> M4[Module 4<br>Step Functions Agent<br>Orchestration]
```

## Tool Use — Request/Response Cycle

```mermaid
sequenceDiagram
    participant App as Agent Application
    participant FM as Foundation Model<br>Bedrock Converse API

    App->>FM: User prompt + toolConfig
    FM-->>App: stopReason: tool_use<br>toolName + input
    App->>App: Execute tool locally
    App->>FM: Tool result
    FM-->>App: stopReason: tool_use<br>(another tool needed)
    App->>App: Execute tool locally
    App->>FM: Tool result
    FM-->>App: stopReason: end_turn<br>Final response
```

## Code-Based Agent Loop (Module 2)

```mermaid
flowchart TD
    Start([User Prompt]) --> Converse[Invoke Converse API<br>with messages + toolConfig]
    Converse --> Check{stopReason?}

    Check -->|end_turn| Return([Return final response])

    Check -->|tool_use| Route{Which tool?}
    Route -->|content_summarizer| CS[Content Summarizer<br>Lambda]
    Route -->|tone_adapter| TA[Tone Adapter<br>Lambda]
    Route -->|post_writer| PW[Post Writer<br>Lambda]

    CS --> Append[Append tool result<br>to message history]
    TA --> Append
    PW --> Append

    Append --> Converse
```

## Step Functions Agent Orchestration (Module 4)

```mermaid
flowchart TD
    Start([User Prompt]) --> Invoke[Invoke Model<br>Bedrock Converse via Lambda]

    Invoke --> Decision{Use tool?}

    Decision -->|No — end_turn| Build[Build Response]
    Build --> Done([Return final response])

    Decision -->|Yes — tool_use| GetTool[Get Tool<br>from model response]

    GetTool --> Which{Which tool?}
    Which -->|content_summarizer| CS[Content Summarizer<br>Lambda]
    Which -->|tone_adapter| TA[Tone Adapter<br>Lambda]
    Which -->|post_writer| PW[Post Writer<br>Lambda]

    CS --> AddResult[Add Tool Response<br>to conversation history]
    TA --> AddResult
    PW --> AddResult

    AddResult --> Invoke
```

## Code-Based vs Step Functions Comparison

```mermaid
graph TD
    subgraph Code-Based<br>Module 2
        CL[Lambda runs agent loop]
        CL --> CB[Bedrock Converse API]
        CL --> CT[Tool Lambdas]
        CL -.->|Pays for idle<br>compute time| CL
    end

    subgraph Step Functions<br>Module 4
        SF[State Machine orchestrates]
        SF --> SB[Invoke Model State<br>Bedrock via Lambda]
        SF --> SD{Use tool? Choice State}
        SD --> ST[Tool Lambda States]
        ST --> SA[Add Tool Response State]
        SA --> SB
        SF -.->|Pauses between steps<br>no idle cost| SF
    end
```

## Full Architecture — Social Media Agent

```mermaid
graph TD
    User([User]) -->|Prompt + tone| SFN[Step Functions<br>State Machine]

    SFN --> InvokeModel[Invoke Model<br>Lambda]
    InvokeModel --> Bedrock[Amazon Bedrock<br>Converse API]
    Bedrock --> InvokeModel

    InvokeModel --> SFN

    SFN -->|tool_use| CS[Content Summarizer<br>Lambda]
    SFN -->|tool_use| TA[Tone Adapter<br>Lambda]
    SFN -->|tool_use| PW[Post Writer<br>Lambda]

    CS --> SFN
    TA --> SFN
    PW --> SFN

    SFN -->|end_turn| Response([Social Media Post])
```
