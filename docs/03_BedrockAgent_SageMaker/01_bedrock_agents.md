# Lab 3 - Building Agents on Amazon Bedrock

**Estimated Duration:** 45 minutes

## Introduction

In this lab, you will learn how to build AI agents using Amazon Bedrock to create an AI solution for travel planning. You will start by understanding the core components of Amazon Bedrock agents, learning how to create and configure your first AI agent. As you progress, building on these fundamentals, you will then explore how to develop a collaborative multi-agent system, where three specialized agents work together to provide the travel planning solution.

## What You Will Build

You'll create three interconnected AI agents:

- **Flight Agent**
  - Handles flight-related queries
  - Searches available flights based on criteria
  - Provides pricing information
  - Manages booking operations
- **Weather Agent**
  - Fetches weather forecasts for destinations
  - Provides weather-based travel recommendations
- **Travel Agent**
  - Acts as the supervisor for the Flight and Weather agents
  - Manages communication between agents
  - Processes user requests and orchestrates responses
  - Makes final recommendations based on input from other agents

## Learning Objectives

After completing this module, you will be able to:

- Build specialized AI agents using Amazon Bedrock that can understand and process natural language requests
- Integrate Amazon Bedrock agents with Lambda to fulfill user requests
- Implement multi-agent communication patterns
- Test and interact with your AI agent through the Amazon Bedrock console and a chatbot application

---

# Module 1 - Building Your First Agent

In this module, you'll create an AI agent to handle flight-related operations using Amazon Bedrock by leveraging the following capabilities:

- **Flight Search** - Helps users search for available flights based on their preferences
- **Flight Booking** - Helps users in booking a flight
- **Flight Cancellation** - Helps users to cancel an existing booking

## Agent Architecture

The flight agent is composed by the following components:

- **Amazon Bedrock:** Hosting the agent AI model
- **AWS Lambda:** Execute the business rules and serve as an integration layer
- **Flight Service:** An external REST API providing flight management capabilities

> You will create the Amazon Bedrock agent only. We will provide the other components needed.

## Create the Agent

1. Navigate to the Amazon Bedrock console
2. In the left navigation pane, click **Agents**
3. Click **Create agent**
4. For **Name**, enter `flight-agent`
5. For **Description**, enter `Enable flight management activities such as searching, booking, and canceling flights`
6. Leave the rest as default and click **Create**

## Customize the Agent

1. Under the **Agent details** section:
   - For **Agent resource**, select *Use an existing service role* and enter the role prefixed with `lab3-bedrock-BedrockAgentRole`
   - In the **Select model** dropdown, select **Amazon - Nova Pro 1.0** and click **Apply**
   - For **Instructions for the Agent**, enter:

     > You are a flight booking specialist with expertise in finding and managing flights based on user preferences. Your task is to search for available flights, book flights, and cancel reservations as needed. When searching for flights, consider the user's preferred origin, destination, departure, and return dates, and any specified preferences such as airline or price range. When booking a flight, ensure the correct flight details are used and confirm the reservation. When canceling a flight, verify the confirmation details before processing the request. Ensure all responses are clear, accurate, and optimized for a seamless travel booking experience.

2. Click **Save** on the top

## Configure Action Group

1. In the **Action groups** section, click **Add**
2. For **Action group name**, enter `FlightManagement`
3. For **Action group invocation**, select *Select an existing Lambda function*
4. In the **Lambda function** dropdown, select `bedrock-flight-agent`

### Action Group Function 1: Flight Search

Switch to JSON Editor mode and paste the following:

```json
{
  "name": "FlightSearch",
  "description": "Search for available flights",
  "parameters": {
    "returnDate": {
      "description": "return date in ISO 8601 format",
      "required": "True",
      "type": "string"
    },
    "origin": {
      "description": "origin airport code",
      "required": "True",
      "type": "string"
    },
    "destination": {
      "description": "destination airport code",
      "required": "True",
      "type": "string"
    },
    "departureDate": {
      "description": "departure date in ISO 8601 format",
      "required": "True",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```

### Action Group Function 2: Flight Booking

Click **Add action group function**, switch to JSON Editor mode, and paste:

```json
{
  "name": "FlightBooking",
  "description": "Book a flight",
  "parameters": {
    "flightId": {
      "description": "unique flight identifier",
      "required": "True",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```

### Action Group Function 3: Flight Cancellation

Click **Add action group function**, switch to JSON Editor mode, and paste:

```json
{
  "name": "FlightCancellation",
  "description": "Cancel a flight",
  "parameters": {
    "confirmation": {
      "description": "flight confirmation identifier",
      "required": "True",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```

## Deploying the Agent

Save the configuration and prepare the agent for testing:

1. Click **Create** to save the action group
2. Click **Save and exit** to save the agent
3. In the Test panel at the right, click **Prepare alias**
4. In the **Aliases** section, click **Create**
5. For **Alias name**, enter `dev`
6. Click **Create alias**

> To deploy your agent, you must create an alias. Aliases are important because:
> - They provide a stable reference point for your agent
> - They allow you to manage different versions of your agent
> - They enable you to deploy updates without changing integration points

## Understanding Action Fulfilment with AWS Lambda

Now let's review how to use Lambda to fulfill the agent actions. This is the same function referenced when we configured the Action group.

When Amazon Bedrock invokes the Lambda function specified in the action group, it provides as input event the user prompt and relevant metadata to execute the action.

Here is an example of input event for the FlightSearch action:

```javascript
{
   messageVersion: '1.0',
   function: 'FlightSearch',
   parameters: [
      { name: 'returnDate', type: 'String', value: '2025-04-02' },
      { name: 'origin', type: 'String', value: 'SFO' },
      { name: 'destination', type: 'String', value: 'LAX' },
      { name: 'departureDate', type: 'String', value: '2025-04-01' }
   ],
   sessionId: '1461a049-e61a-4c9c-be1c-3df576712d69',
   agent: {
      name: 'flight-agent',
      version: '1',
      id: 'Z7FHURX5OS',
      alias: 'QO3FYAYSXN'
   },
   actionGroup: 'FlightManagement',
   sessionAttributes: {},
   promptSessionAttributes: {},
   inputText: 'Please search for round-trip flights from SFO to LAX departing on April 1st and returning April 2nd.'
}
```

To execute the action, first parse the input parameters from `event.parameters`:

```javascript
const parameters = {};
for (const parameter of event.parameters) {
    parameters[parameter.name] = parameter.value;
}
```

Next, identify which action should be performed based on `event.function` and route the request to the appropriate business method. This is necessary as an action group can have multiple actions:

```javascript
let result;

switch (event.function) {
   case 'FlightSearch':
      const search = {
         origin: parameters.origin,
         destination: parameters.destination,
         departureDate: parameters.departureDate,
         returnDate: parameters.returnDate
      };
      console.log('Searching flight: ', search);
      result = await flightSearch(search);
      break;

   case 'FlightBooking':
      const flight = {
         id: parameters.flightId
      };
      console.log('Reserving flight: ', flight);
      result = await flightBook(flight);
      break;

   case 'FlightCancellation':
      const reserve = {
         confirmation: parameters.confirmation
      };
      console.log('Cancelling flight: ', reserve);
      result = await flightCancel(reserve);
      break;

   default:
      throw new Error('Function not supported');
}
```

Finally, wrap the result in the format expected by the Amazon Bedrock agent and return the response:

```javascript
console.log('Result: ', result);

const response = {
    messageVersion: event.messageVersion,
    response: {
        actionGroup: event.actionGroup,
        function: event.function,
        functionResponse: {
            responseBody: {
                'TEXT': {
                    body: JSON.stringify(result)
                }
            }
        }
    }
};

return response;
```

In the business method implementation, you can execute any custom logic required to fulfill the action, such as integration with other AWS services or external services. For the Flight Agent implementation, we invoke an external API. To review the full implementation, navigate to the Lambda console and check out the `bedrock-flight-agent` function code.

## Testing the Agent with Amazon Bedrock Console

In the Test panel at the right:

1. Enter the following prompt and click **Run**:

   > What flight options do I have from SFO to JFK departing on June 5th and returning 10th?

2. The agent should respond with a list of available flight options, similar to:

   > I found 3 flight options for your SFO to JFK round trip:
   > - Delta Airlines - $500
   > - United Airlines - $450
   > - American Airlines - $400
   >
   > Would you like to book one of these flights?

3. Let the agent know which one you want to proceed with:

   > Let's book the cheapest one

4. It should confirm the flight for you:

   > Your flight has been successfully booked. The booking locator code is UXLF71. Safe travels!

**Congratulations!** You've successfully created a specialized AI Flight Agent!

---

# Module 2 - Building a Multi-Agent Solution

## Introduction

In this module, you will build a comprehensive multi-agent solution for travel planning using Amazon Bedrock Agents. Multi-agent systems represent a powerful approach where specialized AI agents collaborate to solve complex problems that would be difficult for a single agent to handle effectively.

## What You Will Build

You'll work with three specialized agents that collaborate to create a comprehensive travel planning solution:

- **Flight Agent** - You'll leverage the existing Flight Agent from the previous module, which handles flight searches, bookings, and cancellations
- **Weather Agent** - You'll build a new Weather Agent that provides weather forecasts and historical data for travel destinations
- **Travel Agent** - You'll create a supervisor agent that coordinates between the specialized agents and provides comprehensive travel recommendations

## Benefits of the Multi-Agent Approach

- **Specialization:** Each agent focuses on a specific domain, allowing for deeper expertise
- **Modularity:** Agents can be developed, tested, and updated independently
- **Scalability:** New capabilities can be added by creating additional specialized agents
- **Improved User Experience:** Users interact with a single interface while benefiting from multiple specialized systems

Let's start by building the Weather Agent!

---

# Building the Weather Agent with IaC

In this module, you'll create an agent to handle weather-related operations using Amazon Bedrock by leveraging the following capabilities:

- **Weather Forecast** - Provide users with real-time or future weather forecast
- **Weather History** - Provide users with historical weather data

## Agent Architecture

The weather agent is composed by the following components:

- **Amazon Bedrock:** Hosting the agent AI model
- **AWS Lambda:** Execute the business rules and serve as an integration layer
- **Weather Service:** An external REST API providing weather information

> You will create the Amazon Bedrock agent only. We will provide the other components needed.

## Infrastructure as Code (IaC)

For the Weather Agent, you will use AWS CloudFormation to create the agent with Infrastructure as Code (IaC) instead of setting it up manually through the console. This approach offers several advantages:

- **Reproducibility:** Easily recreate agents across different environments
- **Version control:** Track changes to your agent configurations
- **Automation:** Integrate agent creation into CI/CD pipelines
- **Consistency:** Ensure consistent configuration across deployments

## Understanding the CloudFormation Template

### Parameters

The template accepts as parameter the foundation model ID to use for the agent:

```yaml
Parameters:
  ModelId:
    Type: String
    Default: us.amazon.nova-pro-v1:0
    Description: The foundation model ID to use for the agent
```

### Amazon Bedrock Agent

The core of the template is the agent definition:

```yaml
BedrockAgent:
  Type: AWS::Bedrock::Agent
  Properties:
    AgentName: weather-agent
    AgentResourceRoleArn: !ImportValue BedrockAgentRoleArn
    Description: Allow weather data retrieval such as forecasts and historical data
    FoundationModel: !Ref ModelId
    IdleSessionTTLInSeconds: 1800
    Instruction: |
       You are a weather specialist providing clear weather information to help users make informed travel decisions.
       You can assume the airport code based on a city name.
       For weather forecasts, you can provide expected temperature and any extreme weather alerts that could impact travel.
       For historical weather analysis, you can provide average minimum and maximum temperatures and rainfall volume per month.
    ActionGroups:
      - ActionGroupName: WeatherData
        Description: Action group for weather-related operations
        ActionGroupExecutor:
          Lambda: !ImportValue WeatherAgentFunctionArn
        FunctionSchema:
          Functions:
            - Name: WeatherForecast
              Description: Retrieve real-time or future weather forecast for a given location and date
              Parameters:
                location:
                  Type: string
                  Description: Airport code for the location
                date:
                  Type: string
                  Description: Date of forecast in ISO 8601 format
            - Name: WeatherHistory
              Description: Retrieve historical weather data for a given location
              Parameters:
                location:
                  Type: string
                  Description: Airport code for the location
```

Key components of the agent definition:

- **Basic Properties:** Name, description, foundation model, IAM role, session timeout (30 minutes)
- **Instructions:** Positions the agent as a weather insights specialist for travel planning
- **Action Groups:** Defines capabilities and specifies the Lambda function that executes the actions
- **Function Schema:** Defines two functions (WeatherForecast and WeatherHistory) with their parameters

### Agent Alias

The template also creates an alias for the agent:

```yaml
BedrockAgentAlias:
   Type: AWS::Bedrock::AgentAlias
   Properties:
      AgentAliasName: dev
      AgentId: !GetAtt BedrockAgent.AgentId
      Description: "Development version of the weather agent"
```

## Deploying the Agent

1. Launch the CloudFormation stack in the **US West 2 (Oregon)** region
2. Confirm that you're in the US West 2 (Oregon) region; the template URL should be pre-populated
3. Click **Next**
4. **Stack details:**
   - Stack name: `lab3-weather-agent` (or choose your preferred name)
   - Review the parameters but don't change anything
   - Click **Next**
5. **Configure stack options:**
   - Leave the default settings
   - Check the acknowledgment box for IAM resource creation
   - Click **Next**
6. Click **Submit**
7. The stack creation will take less than a minute. You can monitor the progress in the CloudFormation console.
8. Once completed, navigate to the Amazon Bedrock console and you'll find a new agent named `weather-agent`.

## Testing the Weather Agent

In the Test panel at the right:

1. Enter the following prompt and click **Run**:

   > When's the best time of year to enjoy the beaches in MIA?

2. The agent should respond with a detailed forecast, similar to:

   > The best time of year to enjoy the beaches in Miami is during the spring (March to May) and fall (September to November) seasons. During these months, the weather is warm and dry, with average temperatures ranging from the mid-60s to mid-80s Fahrenheit. The lower rainfall during these periods also makes for ideal beach conditions.

**Congratulations!** You've successfully created a Weather Agent using Infrastructure as Code (IaC)!

---

# Building a Supervisor Agent

In this module, you'll create a supervisor agent that orchestrates interactions between the flight and weather agents for comprehensive travel planning.

## Prerequisites

Before starting this module, ensure you have completed:

- Module 1 - Building your first agent
- Module 2 - Building agent with IaC

## Create the Agent

1. Navigate to the Amazon Bedrock console
2. In the left navigation pane, click **Agents**
3. Click **Create agent**
4. For **Name**, enter `travel-agent`
5. For **Description**, enter `Provide comprehensive travel planning through multi-agent collaboration`
6. Check **Enable multi-agent collaboration** option
7. Click **Create**

## Customize the Agent

1. Under the **Agent details** section:
   - For **Agent resource**, select *Use an existing service role* and enter the role prefixed with `lab3-bedrock-BedrockAgentRole`
   - In the **Select model** dropdown, select **Anthropic - Claude 3.5 Haiku** and click **Apply**
   - For **Instructions for the Agent**, enter:

     > You are a travel agent organizing seamless trip arrangements by managing multiple specialized agents. Your task is to oversee the travel planning process by coordinating flight bookings and weather insights to ensure a smooth travel experience. When a user requests travel assistance, retrieve flight options based on their preferences, verify weather conditions for the destination, and provide recommendations accordingly. If extreme weather conditions may impact travel, suggest alternative dates or destinations. Ensure that all flight bookings and cancellations are handled efficiently while keeping the traveler informed of any potential disruptions. Your goal is to provide a well-coordinated and stress-free travel experience through effective agent collaboration.

2. Click **Save** on the top

## Configure Multi-Agent Collaboration

1. In the **Multi-agent collaboration** section, click **Edit**
2. Enable the toggle switch **Multi-agent collaboration**
3. In the **Agent collaborator** panel, add the agents:

   **Flight Agent:**
   - In the **Collaborator agent** dropdown, select `flight-agent`
   - In the **Agent alias** dropdown, select `dev`
   - For **Collaborator name**, enter `flight-agent`
   - For **Instructions for the Agent**, enter: `Use flight-agent for flight management activities like search, book or cancel a flight`

   **Weather Agent:**
   - In the **Collaborator agent** dropdown, select `weather-agent`
   - In the **Agent alias** dropdown, select `dev`
   - For **Collaborator name**, enter `weather-agent`
   - For **Instructions for the Agent**, enter: `Use weather-agent for weather data retrieval such as forecasts and historical weather data`

## Saving the Changes

1. Click **Save and exit** to save the multi-agent collaboration
2. Click **Save and exit** again to save the travel agent
3. In the Test panel at the right, click **Prepare**
4. In the **Aliases** section, click **Create**
5. For **Alias name**, enter `dev`
6. Click **Create alias**

## Testing the Travel Agent

Next, you'll use a chatbot application to test the travel agent from a user's perspective.

### Configuring the Chatbot Application

The chatbot uses a Lambda function called `appsync-bedrock-resolver` to communicate with the agent. You'll need to provide your agent's identification so the function can invoke it properly:

1. Take note of the **Agent ID** and **Alias ID**
2. Open the AWS Lambda console
3. Locate and open the function named `appsync-bedrock-resolver`
4. Navigate to the **Configuration** tab and find **Environment variables**
5. Set the environment variables:
   - `AGENT_ID`: Use your Travel Agent's ID
   - `AGENT_ALIAS_ID`: Use your Travel Agent's alias ID
6. Navigate to the chatbot application (locate the `WebSiteUrl` output from the workshop page or CloudFormation Stack Outputs)
7. Authenticate using the pre-created credentials:
   - Username: `workshop_user`
   - Password: `Password1!`

### Interacting with the Agent

In the chatbot application, select the **Chatbot** option under **Bedrock Agents** from the left hand pane.

1. Ask for a trip leaving on the 1st of any month:

   > I need help planning a trip from San Francisco to Los Angeles, departing December 1st and returning the following day.

   Our weather service always issues an alert on the 1st of each month — let's see how the agent handles it.

2. The agent should find a potential disruption and provide recommendations, similar to:

   > ✈️ **Flight Options:**
   > - Delta Airlines - $775
   > - United Airlines - $660
   > - American Airlines - $370
   >
   > ⚠️ **Weather Alerts:**
   > - Severe Thunderstorm Warnings are in effect for both San Francisco and Los Angeles on December 1st
   > - Temperatures will range from 50-71°F
   > - December 2nd shows no weather alerts for Los Angeles
   >
   > **Recommendations:**
   > - Consider the American Airlines flight for the best price
   > - Be prepared for potential flight delays due to thunderstorm warnings
   > - Pack layers and a light waterproof jacket
   > - Check for real-time flight updates closer to your travel date

## Test and Troubleshoot Agent Behavior

One neat feature about Amazon Bedrock Agents is the ability to provide agent reasoning, which significantly enhances testability and troubleshooting. Developers can inspect how the agent interprets inputs, selects actions, and executes API calls. This makes it easier to identify issues, debug unexpected behaviors, and refine prompts or configurations. Additionally, structured reasoning allows for step-by-step validation, helping teams isolate failures, optimize responses, and ensure the agent behaves reliably in different scenarios.

We activate this feature by setting the `enableTrace` flag when calling the Amazon Bedrock Agent API from the `appsync-bedrock-resolver` Lambda function. To view the trace output in the chatbot, click on the **Expand Reasoning** link.

**Congratulations!** You've successfully created a Travel Agent that orchestrates multiple specialized agents!

---

# Summary

Throughout this module, you gained hands-on experience creating and configuring Amazon Bedrock agents with different capabilities and complexity levels. You learned how to define agent instructions that guide behavior, create action groups with structured function schemas, and connect agents to Lambda functions that execute business logic and integrate with external services. You explored how to test agents with real-world queries, orchestrate multiple agents to work together for complex scenarios, and deploy agents using Infrastructure as Code with AWS CloudFormation. These skills provide a foundation for building sophisticated AI workflows that combine the natural language understanding of large language models with structured business processes.

## Key Concepts

- **Agent Design:** Structuring agents with appropriate instructions and action groups
- **Function Schemas:** Defining parameters for agent actions
- **Lambda Integration:** Connecting agents to business logic through Lambda functions
- **Agent Orchestration:** Combining specialized agents for comprehensive solutions
- **Infrastructure as Code:** Deploying and managing agents using CloudFormation
