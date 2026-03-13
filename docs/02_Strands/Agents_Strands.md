# Agents with Strands

---

## Module 1 — Building the Agent

Deploy an Agent built with Strands on AWS Lambda and test it.

### Steps

1. Open the [AWS Lambda Console](https://console.aws.amazon.com/lambda) → `strands-travel-agent` function
2. Paste the code below into the Lambda code editor
3. Click **Deploy**

### Code Breakdown

- Import Strands Agents dependencies
- `TRAVEL_AGENT_PROMPT` defines how the travel agent behaves and which tools it uses
- A local `flight_search` tool simulates a flight search query (in production this would hit a real database)
- The `handler` receives the event payload, creates the agent with the prompt and tool, and returns the response
- The agent uses a Foundation Model on Amazon Bedrock via the Strands SDK ([customization docs](https://strandsagents.com))

```python
from strands import Agent, tool
from typing import Dict, Any

TRAVEL_AGENT_PROMPT = """You are a travel assistant that can help customers book their travel. 

Think step-by-step.

If a customer wants to book their travel, assist them with flight options for their destination.

Use the flight_search tool to provide flight carrier choices for their destination.

Provide the users with a friendly customer support response that includes available flights for their destination.
"""

@tool
def flight_search(city: str) -> dict:
    """Get available flight options to a city.

    Args:
        city: The name of the city
    """
    flights = {
        "Atlanta": [
            "Delta Airlines",
            "Spirit Airlines"
        ],
        "Seattle": [
            "Alaska Airlines",
            "Delta Airlines"
        ],
        "New York": [
            "United Airlines",
            "JetBlue"
        ]
    }
    return flights[city]


def handler(event: Dict[str, Any], _context) -> str:
    travel_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=TRAVEL_AGENT_PROMPT,
        tools=[flight_search]
    )

    response = travel_agent(event.get('prompt'))
    return str(response)
```

### Foundation Model

Configuring your agent to use a specific Foundation Model is as easy as passing in the model ID when creating the Agent. Evaluate models based on response quality, cost, and latency.

### Testing

1. Click the **Test** tab above the code editor
2. Event name: `Test`
3. Event JSON:
```json
{
    "prompt": "Can you tell me travel options to Seattle?"
}
```
4. Click **Save** and **Test**

Expected response:
> Alaska Airlines, Delta Airlines

---

## Module 2 — Integration with External APIs

Update the agent to add weather forecasts using the National Weather Service API and use a different Foundation Model.

### What Changes

- Updated `TRAVEL_AGENT_PROMPT` to include weather forecast behavior
- Added the built-in `http_request` tool from `strands-tools`

### Steps

1. Update the Lambda code with the following
2. Click **Deploy**

```python
from strands import Agent, tool
from strands_tools import http_request
from typing import Dict, Any

TRAVEL_AGENT_PROMPT = """You are a travel assistant that can help customers book their travel. 

Think step-by-step.

If a customer wants to book their travel, assist them with flight options for their destination and provide them with information about the weather.

Use the flight_search tool to provide flight carrier choices for their destination.

You can provide information about the weather with the following:
1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States
4. The Seattle zip code value is 98101 and the latitude and longitude coordinates are 47.6061° N, 122.3328° W
5. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
6. Then use the returned forecast URL to get the actual forecast
When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.

Provide the users with a friendly customer support response that includes available flights and the weather for their destination.

"""

@tool
def flight_search(city: str) -> dict:
    """Get available flight options to a city.

    Args:
        city: The name of the city
    """
    flights = {
        "Atlanta": [
            "Delta Airlines",
            "Spirit Airlines"
        ],
        "Seattle": [
            "Alaska Airlines",
            "Delta Airlines"
        ],
        "New York": [
            "United Airlines",
            "JetBlue"
        ]
    }
    return flights[city]


def handler(event: Dict[str, Any], _context) -> str:
    travel_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=TRAVEL_AGENT_PROMPT,
        tools=[flight_search, http_request]
    )

    response = travel_agent(event.get('prompt'))
    return str(response)
```

### Testing

1. Click the **Test** tab
2. Event JSON:
```json
{
    "prompt": "Can you tell me travel options to Seattle?"
}
```
3. Click **Save** and **Test**

Expected response includes flight options **and** a weather forecast for Seattle.

---

## Module 3 — Adding Agent Memory

Session management lets the agent remember past interactions using a unique session ID.

### How It Works

- Each conversation gets a unique session ID
- Using the same session ID across requests maintains continuity
- Conversation history is stored externally (S3) for persistence and scalability

### Steps

1. Update the Lambda code with the following (uses Strands built-in `S3SessionManager`)
2. Click **Deploy**

```python
from strands import Agent, tool
from strands_tools import http_request
from strands.session.s3_session_manager import S3SessionManager
from typing import Dict, Any
import boto3
import os
import json

TRAVEL_AGENT_PROMPT = """You are a travel assistant that can help customers book their travel. 

Think step-by-step.

If a customer wants to book their travel, assist them with flight options for their destination and provide them with information about the weather.

Use the flight_search tool to provide flight carrier choices for their destination.

You can provide information about the weather with the following:
1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States
4. The Seattle zip code value is 98101 and the latitude and longitude coordinates are 47.6061° N, 122.3328° W
5. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
6. Then use the returned forecast URL to get the actual forecast
When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.

Provide the users with a friendly customer support response that includes available flights and the weather for their destination.

"""

@tool
def flight_search(city: str) -> dict:
    """Get available flight options to a city.

    Args:
        city: The name of the city
    """
    flights = {
        "Atlanta": [
            "Delta Airlines",
            "Spirit Airlines"
        ],
        "Seattle": [
            "Alaska Airlines",
            "Delta Airlines"
        ],
        "New York": [
            "United Airlines",
            "JetBlue"
        ]
    }
    return flights[city]


def handler(event: Dict[str, Any], _context) -> str:
    session_manager = S3SessionManager(
        session_id=event["user"]["session_id"],
        bucket=os.environ['SESSIONS_BUCKET'],
        prefix="agent-sessions"
    )
    travel_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=TRAVEL_AGENT_PROMPT,
        tools=[flight_search, http_request],
        session_manager=session_manager
    )
    response = travel_agent(event.get('prompt'))
    return str(response)
```

### Testing Memory

**Test 1** — Ask about Seattle:
```json
{
    "prompt": "Can you tell me travel options to Seattle?",
    "user": { "session_id": "123" }
}
```

**Test 2** — Follow-up without mentioning Seattle:
```json
{
    "prompt": "Can you tell me some local things to do?",
    "user": { "session_id": "123" }
}
```

The agent should respond with Seattle-specific local attractions — it remembers the context from the previous message.

Session history is stored in the S3 bucket prefixed with `lab2-strands-travelagents3sessionsbucket` under `agent-sessions/`.

---

## Module 4 — Using Bedrock Knowledge Bases for RAG

Use Amazon Bedrock Knowledge Bases to give the agent access to private data sources via the `retrieve` tool.

### Step 1: Upload Sample Data to S3

Open AWS CloudShell and run:

```bash
BUCKET=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, 'lab2-strands-travelagents3bucketrag')].Name" --output text)
aws s3 cp s3://ws-assets-prod-iad-r-pdx-f3b3f9f1a7d6a3d0/eb18d538-bf1f-49b9-9747-c474953deee1/seattletouroperators.txt .
cat seattletouroperators.txt
aws s3 cp seattletouroperators.txt s3://$BUCKET/
```

### Step 2: Create the Knowledge Base

1. Open the [Amazon Bedrock console](https://console.aws.amazon.com/bedrock)
2. Navigate to **Knowledge bases** → **Create** → **Knowledge Base with vector store**
3. Knowledge base details:
   - Name: `StrandsTravelAgentKB`
   - IAM role: select existing role starting with `lab2-strands-BedrockKnowledgeBaseRole`
   - Data source type: **S3**
   - Click **Next**
4. Data source configuration:
   - Name: `TravelAgentS3DataSource`
   - Browse S3 → select bucket with prefix `lab2-strands-travelagents3bucketrag`
   - Click **Next**
5. Data storage and processing:
   - Embedding model: **Amazon Titan Text Embeddings v2**
   - Vector store: **Amazon S3 Vectors** (Quick create)
   - Click **Next**
6. Review and click **Create knowledge base**

### Step 3: Sync the Data Source

- In the **Data sources** section, find `TravelAgentS3DataSource`
- Click **Sync** and wait for status to become "Available"

### Step 4: Copy the Knowledge Base ID

- Copy the **Knowledge base ID** from the overview section (e.g. `ABCDEFGHIJ`)

### Update the Agent

**Environment variable:**
1. Lambda Console → `strands-travel-agent` → **Configuration** → **Environment variables**
2. Set `KNOWLEDGE_BASE_ID` to the ID from Step 4
3. Click **Save**

**Lambda code** — adds the `retrieve` tool and updated prompt:

```python
from strands import Agent, tool
from strands_tools import http_request, retrieve
from strands.session.s3_session_manager import S3SessionManager
from typing import Dict, Any
import boto3
import os
import json

TRAVEL_AGENT_PROMPT = """You are a travel assistant that can help customers book their travel. 

Think step-by-step.

If a customer wants to book their travel, assist them with flight options for their destination and provide them with information about the weather.

Use the flight_search tool to provide flight carrier choices for their destination.

Use the retrieve tool to get validated list of tour operators for different kinds of tours and activities that we support.

You can provide information about the weather with the following:
1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States
4. The Seattle zip code value is 98101 and the latitude and longitude coordinates are 47.6061° N, 122.3328° W
5. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
6. Then use the returned forecast URL to get the actual forecast
When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.

Provide the users with a friendly customer support response that includes available flights and the weather for their destination.

"""

@tool
def flight_search(city: str) -> dict:
    """Get available flight options to a city.

    Args:
        city: The name of the city
    """
    flights = {
        "Atlanta": [
            "Delta Airlines",
            "Spirit Airlines"
        ],
        "Seattle": [
            "Alaska Airlines",
            "Delta Airlines"
        ],
        "New York": [
            "United Airlines",
            "JetBlue"
        ]
    }
    return flights[city]


def handler(event: Dict[str, Any], _context) -> str:
    session_manager = S3SessionManager(
        session_id=event["user"]["session_id"],
        bucket=os.environ['SESSIONS_BUCKET'],
        prefix="agent-sessions"
    )
    travel_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=TRAVEL_AGENT_PROMPT,
        tools=[flight_search, http_request, retrieve],
        session_manager=session_manager
    )
    response = travel_agent(event.get('prompt'))
    return str(response)
```

### Testing

```json
{
    "prompt": "What are some tour operators with water activities?",
    "user": { "session_id": "123" }
}
```

The agent should return approved tour operators from the knowledge base.

---

## Module 5 — Using MCP

Use the MCP Client Tool in Strands to connect to external MCP Servers and dynamically load remote tools.

### Architecture

The `strands-travel-agent` Lambda (MCP Client) calls an Attractions MCP Server created via AgentCore Gateway. The MCP Server is secured with OAuth2 (Cognito). The Attractions Lambda exposes tools: `list_attractions`, `reserve_ticket`, and `cancel_ticket`.

### Step 1: Create the AgentCore Gateway

1. Open the [Amazon Bedrock AgentCore console](https://console.aws.amazon.com/bedrock/agentcore)
2. **Gateways** → **Create gateway**
   - Name: `TravelAttractionsGateway`
   - Keep **Quick create with Cognito** selected
   - IAM role: select existing role starting with `lab2-strands-AgentCoreGatewayExecutionRole`
3. Target Details:
   - Name: `TravelAttractionsLambdaTarget`
   - Description: `Lambda function which handles Travel Attractions`
   - Type: **Lambda ARN**
   - ARN: copy from Lambda Console → `attractions` function
   - Schema: **Define an inline schema** — paste the following:

```json
[
  {
    "description": "List available times and price for attractions",
    "inputSchema": {
      "properties": {
        "date": {
          "description": "Requested date for attraction",
          "type": "string"
        }
      },
      "required": ["date"],
      "type": "object"
    },
    "name": "list_attractions"
  },
  {
    "description": "Reserve attraction ticket for a date and time",
    "inputSchema": {
      "properties": {
        "attraction": {
          "description": "The attraction to reserve",
          "type": "string"
        },
        "date": {
          "description": "The available date for the attraction",
          "type": "string"
        },
        "time": {
          "description": "The available time for the attraction",
          "type": "string"
        }
      },
      "required": ["attraction", "date", "time"],
      "type": "object"
    },
    "name": "reserve_ticket"
  },
  {
    "description": "Cancel ticket reservation",
    "inputSchema": {
      "properties": {
        "reservationCode": {
          "description": "Reservation code for reserved attraction",
          "type": "string"
        }
      },
      "required": ["reservationCode"],
      "type": "object"
    },
    "name": "cancel_ticket"
  }
]
```

4. Click **Create gateway**

### Update the Agent for MCP

Update `strands-travel-agent` Lambda with the following code, then click **Deploy**:

```python
from strands import Agent, tool
from strands_tools import http_request, current_time
from strands.session.s3_session_manager import S3SessionManager
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from typing import Dict, Any
import os
import requests

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
TOKEN_URL = os.environ['DOMAIN_URL'] + '/oauth2/token'
GATEWAY_URL = os.environ['GATEWAY_URL']

TRAVEL_AGENT_PROMPT = """You are a travel assistant that can help customers book their travel. 

Think step-by-step.

Use the flight_search tool to provide flight carrier choices for their destination.

Use list_attractions, reserve_ticket and cancel_ticket tools to provide attractions management service.

You can provide information about the weather with the following:
1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States
4. The Seattle zip code value is 98101 and the latitude and longitude coordinates are 47.6061° N, 122.3328° W
5. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
6. Then use the returned forecast URL to get the actual forecast
When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.

Provide the users with a friendly customer support response that includes available flights and the weather for their destination.

"""

@tool
def flight_search(city: str) -> dict:
    """Get available flight options to a city.

    Args:
        city: The name of the city
    """
    flights = {
        "Atlanta": [
            "Delta Airlines",
            "Spirit Airlines"
        ],
        "Seattle": [
            "Alaska Airlines",
            "Delta Airlines"
        ],
        "New York": [
            "United Airlines",
            "JetBlue"
        ]
    }
    return flights[city]

def fetch_access_token(client_id, client_secret, token_url):
  response = requests.post(
    token_url,
    data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  return response.json()['access_token']

def create_streamable_http_transport(mcp_url: str, access_token: str):
       return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})


def handler(event: Dict[str, Any], _context) -> str:
    session_manager = S3SessionManager(
        session_id=event["user"]["session_id"],
        bucket=os.environ['SESSIONS_BUCKET'],
        prefix="agent-sessions"
    )

    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    mcp_client = MCPClient(lambda: create_streamable_http_transport(GATEWAY_URL, access_token))
       
    with mcp_client:
        tools_mcp = mcp_client.list_tools_sync()

        tools_mcp += [flight_search, http_request, current_time]

        travel_agent = Agent(
            model="us.amazon.nova-lite-v1:0",
            system_prompt=TRAVEL_AGENT_PROMPT,
            tools= tools_mcp,
            session_manager=session_manager
        )
        response = travel_agent(event.get('prompt')) 

    return str(response)
```

### Set Environment Variables

In CloudShell, run:

```bash
aws s3 cp s3://ws-assets-prod-iad-r-pdx-f3b3f9f1a7d6a3d0/eb18d538-bf1f-49b9-9747-c474953deee1/lab2/agentcore_gateway_info.sh . && chmod +x agentcore_gateway_info.sh
./agentcore_gateway_info.sh
```

Then in Lambda → **Configuration** → **Environment variables**, update `CLIENT_ID`, `CLIENT_SECRET`, `DOMAIN_URL`, and `GATEWAY_URL` with the output values. Click **Save**.

### Testing

```json
{
    "prompt": "Reserve a ticket for Space needle for 9:00 AM tomorrow",
    "user": { "session_id": "123" }
}
```

Expected response confirms the reservation with a reservation code.

---

## Module 6 — Exposing the Agent via API Gateway

Expose the Strands agent through Amazon API Gateway with Cognito authentication.

### Step 1: Create the REST API

1. [API Gateway Console](https://console.aws.amazon.com/apigateway) → **Create API** → **REST API** → **Build**
2. Choose **New API**
   - Name: `strands-travel-agent`
   - Description: `API for Strands Travel Agent`
   - Endpoint Type: **Regional**
3. Click **Create API**

### Step 2: Create the `/chat` Resource

1. **Resources** → select root `/` → **Create Resource**
   - Resource Name: `chat`
   - Resource Path: `/`
2. Click **Create Resource**

### Step 3: Create the POST Method

1. Select `/chat` → **Create Method** → **POST**
   - Integration type: **Lambda Function**
   - Lambda Proxy integration: **Enabled**
   - Lambda Function: `strands-travel-agent`
2. Click **Create Method**

### Step 4: Create the Cognito Authorizer

1. **Authorizers** → **Create authorizer**
   - Name: `CognitoAuthorizer`
   - Type: **Cognito**
   - User Pool: `StrandsAgentUserPool`
   - Token Source: `Authorization`
2. Click **Create Authorizer**

### Step 5: Add Authorization to the Method

1. **Resources** → select POST under `/chat` → **Method Request** → **Edit**
2. Set Authorization to `CognitoAuthorizer`
3. Click **Save**

### Step 6: Deploy the API

1. **Deploy API** → New Stage → Stage name: `prod`
2. Click **Deploy**

### Step 7: Update Lambda for API Gateway

Update `strands-travel-agent` with the following code, then click **Deploy**:

```python
from strands import Agent, tool
from strands_tools import http_request, current_time
from strands.session.s3_session_manager import S3SessionManager
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from typing import Dict, Any
import os
import requests
import json
import re

THINKING_PATTERN = r'<thinking>.*?</thinking>'
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
TOKEN_URL = os.environ['DOMAIN_URL'] + '/oauth2/token'
GATEWAY_URL = os.environ['GATEWAY_URL']

TRAVEL_AGENT_PROMPT = """You are a travel assistant that can help customers book their travel. 

Think step-by-step.

Use the flight_search tool to provide flight carrier choices for their destination.

Use list_attractions, reserve_ticket and cancel_ticket tools to provide attractions management service.

You can provide information about the weather with the following:
1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States
4. The Seattle zip code value is 98101 and the latitude and longitude coordinates are 47.6061° N, 122.3328° W
5. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
6. Then use the returned forecast URL to get the actual forecast
When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.

Provide the users with a friendly customer support response that includes available flights and the weather for their destination.

"""

@tool
def flight_search(city: str) -> dict:
    """Get available flight options to a city.

    Args:
        city: The name of the city
    """
    flights = {
        "Atlanta": [
            "Delta Airlines",
            "Spirit Airlines"
        ],
        "Seattle": [
            "Alaska Airlines",
            "Delta Airlines"
        ],
        "New York": [
            "United Airlines",
            "JetBlue"
        ]
    }
    return flights[city]

def fetch_access_token(client_id, client_secret, token_url):
  response = requests.post(
    token_url,
    data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  return response.json()['access_token']

def create_streamable_http_transport(mcp_url: str, access_token: str):
       return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})


def handler(event: Dict[str, Any], _context) -> str:
    session_manager = S3SessionManager(
        session_id=event["requestContext"]["authorizer"]["claims"]["cognito:username"],
        bucket=os.environ['SESSIONS_BUCKET'],
        prefix="agent-sessions"
    )

    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    mcp_client = MCPClient(lambda: create_streamable_http_transport(GATEWAY_URL, access_token))
       
    with mcp_client:
        tools_mcp = mcp_client.list_tools_sync()

        tools_mcp += [flight_search, http_request, current_time]

        travel_agent = Agent(
            model="us.amazon.nova-lite-v1:0",
            system_prompt=TRAVEL_AGENT_PROMPT,
            tools= tools_mcp,
            session_manager=session_manager
        )
        body = json.loads(event['body'])
        response = travel_agent(body['prompt'])
     
    return {
        'statusCode': 200,
        'body': json.dumps({
            'response': re.sub(THINKING_PATTERN, '', str(response), flags=re.DOTALL).strip()
        })
    }
```

Key changes: parses prompt from `body`, uses the authenticated Cognito username as `session_id` for proper user isolation, and strips `<thinking>` tags from the response.

### Testing the API

**Create a test user in CloudShell:**

```bash
USER_POOL_ID=$(aws cognito-idp list-user-pools --max-results 20 --query 'UserPools[?Name==`StrandsAgentUserPool`].Id' --output text)
CLIENT_ID=$(aws cognito-idp list-user-pool-clients --user-pool-id $USER_POOL_ID --query 'UserPoolClients[0].ClientId' --output text)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --user-attributes Name=email,Value=test@example.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS > /dev/null

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --password "MyPassword123!" \
  --permanent > /dev/null

TOKEN_RESPONSE=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id $USER_POOL_ID \
  --client-id $CLIENT_ID \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=testuser,PASSWORD="MyPassword123!")

ID_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.AuthenticationResult.IdToken')
echo "ID Token: $ID_TOKEN"
```

**Get the Invoke URL:**
- API Gateway → **Stages** → `prod` → `/chat` → POST → copy the **Invoke URL**

**Test the API:**

```bash
API_URL=REPLACE_BY_INVOKE_URL

curl -X POST $API_URL \
  -H "Authorization: $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Can you tell me travel options to Seattle?"}' | jq
```

Expected response:
```json
{
  "response": "Hi there! I found that you can fly to Seattle with Alaska Airlines or Delta Airlines. Would you also like to know about attractions in Seattle? Also, do you need the weather forecast for your trip?"
}
```

Your agent is now accessible via HTTP and can be integrated into web apps, mobile apps, or other services.
