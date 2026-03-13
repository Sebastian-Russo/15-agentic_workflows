# Bedrock Agents — Flow Diagrams

## Module Progression

```mermaid
graph LR
    M1[Module 1<br>Flight Agent<br>Console] --> M2[Module 2<br>Weather Agent<br>CloudFormation]
    M2 --> M3[Module 3<br>Travel Agent<br>Multi-Agent Supervisor]
```

## Flight Agent — Single Agent Flow

```mermaid
graph TD
    User([User]) -->|Prompt| Agent[Flight Agent<br>Amazon Nova Pro 1.0]

    Agent -->|Selects action| AG[Action Group<br>FlightManagement]

    AG --> Lambda[bedrock-flight-agent<br>Lambda]

    Lambda -->|event.function| Switch{Route by Function}
    Switch -->|FlightSearch| FS[Flight Search API]
    Switch -->|FlightBooking| FB[Flight Booking API]
    Switch -->|FlightCancellation| FC[Flight Cancel API]

    FS --> Result[Format Response]
    FB --> Result
    FC --> Result

    Result --> Lambda
    Lambda --> Agent
    Agent -->|Natural language response| User
```

## Weather Agent — Single Agent Flow

```mermaid
graph TD
    User([User]) -->|Prompt| Agent[Weather Agent<br>Amazon Nova Pro 1.0]

    Agent -->|Selects action| AG[Action Group<br>WeatherData]

    AG --> Lambda[bedrock-weather-agent<br>Lambda]

    Lambda --> Switch{Route by Function}
    Switch -->|WeatherForecast| WF[Weather Forecast API]
    Switch -->|WeatherHistory| WH[Weather History API]

    WF --> Result[Format Response]
    WH --> Result

    Result --> Lambda
    Lambda --> Agent
    Agent -->|Natural language response| User
```

## Multi-Agent — Travel Agent Supervisor

```mermaid
graph TD
    User([User]) -->|Travel request| TA[Travel Agent<br>Supervisor<br>Claude 3.5 Haiku]

    TA -->|Flight queries| FA[Flight Agent<br>Amazon Nova Pro 1.0]
    TA -->|Weather queries| WA[Weather Agent<br>Amazon Nova Pro 1.0]

    FA --> FAG[FlightManagement<br>Action Group]
    FAG --> FLambda[bedrock-flight-agent<br>Lambda]
    FLambda --> FAPI[Flight Service API]

    WA --> WAG[WeatherData<br>Action Group]
    WAG --> WLambda[bedrock-weather-agent<br>Lambda]
    WLambda --> WAPI[Weather Service API]

    FAPI --> FLambda --> FA --> TA
    WAPI --> WLambda --> WA --> TA

    TA -->|Combined recommendation| User
```

## Lambda Action Fulfillment Flow

```mermaid
sequenceDiagram
    participant A as Bedrock Agent
    participant L as Lambda Function
    participant API as External Service

    A->>L: Invoke with event<br>(function, parameters, inputText)
    L->>L: Parse event.parameters
    L->>L: Route by event.function
    L->>API: Call external service
    API-->>L: Service response
    L->>L: Wrap in responseBody format
    L-->>A: {actionGroup, function, functionResponse}
    A->>A: Generate natural language response
```

## Chatbot Application Flow (Module 3)

```mermaid
graph LR
    User([User]) --> Chat[Chatbot App]
    Chat --> AppSync[AWS AppSync]
    AppSync --> Resolver[appsync-bedrock-resolver<br>Lambda]
    Resolver -->|InvokeAgent API<br>agentId + aliasId| TA[Travel Agent]
    TA --> FA[Flight Agent]
    TA --> WA[Weather Agent]
    FA --> TA
    WA --> TA
    TA --> Resolver
    Resolver --> AppSync
    AppSync --> Chat
    Chat --> User
```

## CloudFormation Deployment (Weather Agent)

```mermaid
graph TD
    CFN[CloudFormation Stack<br>lab3-weather-agent] --> Agent[AWS::Bedrock::Agent<br>weather-agent]
    CFN --> Alias[AWS::Bedrock::AgentAlias<br>dev]

    Agent -->|AgentResourceRoleArn| IAM[Imported IAM Role]
    Agent -->|Lambda| Lambda[Imported Lambda ARN]
    Agent -->|FoundationModel| FM[us.amazon.nova-pro-v1:0]

    Agent --> AG[Action Group: WeatherData]
    AG --> F1[WeatherForecast<br>location, date]
    AG --> F2[WeatherHistory<br>location]

    Alias -->|References| Agent
```
