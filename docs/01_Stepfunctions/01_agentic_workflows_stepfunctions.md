# Lab 1 - Building Agentic Workflows with AWS Step Functions

---

## Module 1 - Understanding Tool Use

**Tool Use** is an Amazon Bedrock feature that allows the agent model to use tools that can help respond to a message. When invoking **Converse** or **InvokeModel** APIs, you can include a list of available tools. If the model decides to use a tool, it pauses the response, returns the tool name and input data, and waits. Your agent application runs the tool, sends the result back to the model, and the model continues the conversation using that result.

![Tool Use - Sequence Diagram](images/tool-use-sequence-diagram.png)

### Example Application

For example, you might have a chat application that lets users find out the most popular song played on a radio station. To answer a request for the most popular song, a model needs a tool that can query and return the song information.

### API Call

The following is a code snippet showing how to use Tool Use with the AWS JavaScript SDK:

```javascript
await bedrockClient.send(new ConverseCommand({
    messages: messages,
    modelId: MODEL_ID,
    system: SYSTEM_PROMPT,
    toolConfig: TOOLS
}));
```

The `toolConfig` parameter is what distinguishes this API invocation to leverage Tool Use. It contains the list of available tools and expected input properties in JSON Schema definition:

```json
{
    "tools": [
        {
            "toolSpec": {
                "name": "top_song",
                "description": "Get the most popular song played on a radio station.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "sign": {
                                "type": "string",
                                "description": "The call sign for the radio station for which you want the most popular song. Example calls signs are WZPZ and WKRP."
                            }
                        },
                        "required": [
                            "sign"
                        ]
                    }
                }
            }
        }
    ]
}
```

### Understanding the Response

Let's say the user asks *"What is the most popular song on the WZPZ?"* and the model chooses to use a tool, it would produce the following response:

```json
{
    "output": {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "toolUse": {
                        "toolUseId": "tooluse_kZJMlvQmRJ6eAyJE5GIl7Q",
                        "name": "top_song",
                        "input": {
                            "sign": "WZPZ"
                        }
                    }
                }
            ]
        }
    },
    "stopReason": "tool_use"
}
```

Notice the `name` property matches the value `top_song` we set in `toolConfig`. The application uses this information to invoke the appropriate tool and send tool response to the model. When the model returns `stopReason` as `end_turn`, the conversation ends:

```json
"stopReason": "end_turn"
```

---

## Module 2 - Coding an Agent with Tool Use

In this module, you will learn how to create an agent using code and Tool Use. The **Social Media Agent** transforms long-form content—blog posts, announcements, or articles—into engaging social media posts. It serves as your personal assistant for creating content that's ready to share.

### Agent Architecture

The agent architecture consists of these components:

- **AWS Lambda**: Runs the agent code and hosts the individual tools
- **Amazon Bedrock**: Provides the AI model for reasoning and decision-making

![Social Media Agent](images/social-media-agent.png)

### The Agent Loop

The agent loop is the core concept that enables intelligent, autonomous behavior through continuous reasoning, tool use, and response generation. This loop continues until the agent gathers all information needed for a complete answer.

![Agent Loop](images/agent-loop.png)

### Agent Code Walkthrough

#### Tool Declaration

To achieve its objective, the agent will have the following tools available:

| Tool                | Description                                                    |
| ------------------- | -------------------------------------------------------------- |
| Content Summarizer  | Extracts key points from long text                             |
| Tone Adapter        | Changes writing style to match your needs (professional, casual, etc.) |
| Post Writer         | Crafts perfect content for social platforms                    |

These tools are declared using JSON Schema as follows:

```javascript
const TOOLS = [
    {"toolSpec": {
        "name": CONTENT_SUMMARIZER_TOOL_NAME,
        "description": "Summarize a text extracting key takeaways",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to be summarized"}
                },
                "required": ["text"]
            }
        }}
    },
    {"toolSpec": {
        "name": TONE_ADAPTER_TOOL_NAME,
        "description": "Tailor a text to a specific tone",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "tone": {"type": "string", "description": "Text tone to be used(e.g., professional, casual, fantasy)"},
                    "text": {"type": "string", "description": "Text to be adapted"}
                },
                "required": ["tone","text"]
            }
        }}
    },
    {"toolSpec": {
        "name": POST_WRITER_TOOL_NAME,
        "description": "Create social media posts",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to used as reference to create the post"}
                },
                "required": ["text"]
            }
        }}
    }];
```

#### Agent Loop Implementation

The heart of our agent is the loop that implements the reasoning cycle. For each iteration the following logic is executed:

1. **AI Reasoning**: The agent thinks about the current situation and decides what to do next
2. **Decision Point**: Two things can happen:
   - **End Turn**: The agent has everything it needs and provides the final answer
   - **Tool Use**: The agent needs more information and calls a tool
3. **Tool Execution**: If tools are needed, we execute them and add results back to the conversation
4. **Continue Loop**: The cycle repeats with new information until complete

```javascript
while(true) {
    // Use Converse API to complete the prompt
    const converse = await invokeConverseAPI(messages);
    const assistantMessage = converse.output.message;
    // Enforce one tool at a time, where 2 == thinking + toolUse
    assistantMessage.content.splice(2); 
    // Add the assistant response in the message history
    messages.push(assistantMessage);

    // Collect the model final response and return to the user
    if (converse.stopReason === 'end_turn') {
        const responseContent = assistantMessage.content[0].text;
        logModelThinking(responseContent);
        const response = responseContent.replace(THINKING_PATTERN, '').trim();
        return {response: response};
    }

    // Invoke the tool specified by the model
    if (converse.stopReason === 'tool_use') {
        const toolResponseMessage = { content: [], role: ConversationRole.USER };
        for (const content of assistantMessage.content) {
            const tool = content.toolUse;
            if (tool) {
                const toolResponse = await invokeTool(tool);
                toolResponseMessage.content.push({
                    toolResult: {
                        toolUseId: tool.toolUseId,
                        content: [{json: toolResponse}]
                    }
                });
            }
        }
        messages.push(toolResponseMessage);
    }
}
```

#### Tool Execution

When the agent decides to use a tool, this function routes the request to the appropriate tool and returns the results back to the agent.

The beauty of this approach is that the agent makes intelligent decisions about which tools to use and when. It might summarize content first, then adapt the tone, and finally create the social media post. Or it might take a different path based on your specific request.

```javascript
async function invokeTool(tool) {
    console.log(`Invoking tool: ${tool.name} (ID: ${tool.toolUseId})`);
    switch (tool.name) {
        case CONTENT_SUMMARIZER_TOOL_NAME:
            return await invokeLambda(CONTENT_SUMMARIZER_FUNCTION, tool.input);
        case TONE_ADAPTER_TOOL_NAME:
            return await invokeLambda(TONE_ADAPTER_FUNCTION, tool.input);
        case POST_WRITER_TOOL_NAME:
            return await invokeLambda(POST_WRITER_FUNCTION, tool.input);
        default:
            throw new Error(`Unknown tool: ${tool.name} (ID: ${tool.toolUseId})`);
    }
}
```

> In this particular implementation, all tools are available as Lambda functions. However, they could be any resource accessible from your code, such as databases, third-party APIs, or AWS APIs.

### Testing

To test the agent you will ask it to create a social media post using a peculiar tone (mythical) from the Amazon Bedrock announcement blog.

1. Navigate to the **Lambda console**
2. Open the function `lab1-social-media-agent`
3. In the **Test** tab, create a new event:
   - For **Event Name**, enter `Test` or a name of your preference
   - For **Event JSON**, enter:

```json
{"prompt": "Please create a social media post using a mythical tone: This April, we announced Amazon Bedrock as part of a set of new tools for building with generative AI on AWS. Amazon Bedrock is a fully managed service that offers a choice of high-performing foundation models (FMs) from leading AI companies, including AI21 Labs, Anthropic, Cohere, Stability AI, and Amazon, along with a broad set of capabilities to build generative AI applications, simplifying the development while maintaining privacy and security.\n\nToday, I'm happy to announce that Amazon Bedrock is now generally available! I'm also excited to share that Meta's Llama 2 13B and 70B parameter models will soon be available on Amazon Bedrock.\n\nAmazon Bedrock's comprehensive capabilities help you experiment with a variety of top FMs, customize them privately with your data using techniques such as fine-tuning and retrieval-augmented generation (RAG), and create managed agents that perform complex business tasks—all without writing any code. Check out my previous posts to learn more about agents for Amazon Bedrock and how to connect FMs to your company's data sources.\n\nNote that some capabilities, such as agents for Amazon Bedrock, including knowledge bases, continue to be available in preview. I'll share more details on what capabilities continue to be available in preview towards the end of this blog post.\n\nSince Amazon Bedrock is serverless, you don't have to manage any infrastructure, and you can securely integrate and deploy generative AI capabilities into your applications using the AWS services you are already familiar with.\n\nAmazon Bedrock is integrated with Amazon CloudWatch and AWS CloudTrail to support your monitoring and governance needs. You can use CloudWatch to track usage metrics and build customized dashboards for audit purposes. With CloudTrail, you can monitor API activity and troubleshoot issues as you integrate other systems into your generative AI applications. Amazon Bedrock also allows you to build applications that are in compliance with the GDPR and you can use Amazon Bedrock to run sensitive workloads regulated under the U.S. Health Insurance Portability and Accountability Act (HIPAA).\n\nGet Started with Amazon Bedrock:\n    You can access available FMs in Amazon Bedrock through the AWS Management Console, AWS SDKs, and open-source frameworks such as LangChain.\n\nIn the Amazon Bedrock console, you can browse FMs and explore and load example use cases and prompts for each model. First, you need to enable access to the models. In the console, select Model access in the left navigation pane and enable the models you would like to access. Once model access is enabled, you can try out different models and inference configuration settings to find a model that fits your use case.\n\nData Privacy and Network Security:\n    With Amazon Bedrock, you are in control of your data, and all your inputs and customizations remain private to your AWS account. Your data, such as prompts, completions, and fine-tuned models, is not used for service improvement. Also, the data is never shared with third-party model providers.\n\nYour data remains in the Region where the API call is processed. All data is encrypted in transit with a minimum of TLS 1.2 encryption. Data at rest is encrypted with AES-256 using AWS KMS managed data encryption keys. You can also use your own keys (customer managed keys) to encrypt the data.\n\nYou can configure your AWS account and virtual private cloud (VPC) to use Amazon VPC endpoints (built on AWS PrivateLink) to securely connect to Amazon Bedrock over the AWS network. This allows for secure and private connectivity between your applications running in a VPC and Amazon Bedrock.\n\nGovernance and Monitoring:\n    Amazon Bedrock integrates with IAM to help you manage permissions for Amazon Bedrock. Such permissions include access to specific models, playground, or features within Amazon Bedrock. All AWS-managed service API activity, including Amazon Bedrock activity, is logged to CloudTrail within your account.\n\nAmazon Bedrock emits data points to CloudWatch using the AWS/Bedrock namespace to track common metrics such as InputTokenCount, OutputTokenCount, InvocationLatency, and (number of) Invocations. You can filter results and get statistics for a specific model by specifying the model ID dimension when you search for metrics. This near real-time insight helps you track usage and cost (input and output token count) and troubleshoot performance issues (invocation latency and number of invocations) as you start building generative AI applications with Amazon Bedrock.\n\nBilling and Pricing Models:\n    Here are a couple of things around billing and pricing models to keep in mind when using Amazon Bedrock:\n\nBilling – Text generation models are billed per processed input tokens and per generated output tokens. Text embedding models are billed per processed input tokens. Image generation models are billed per generated image.\n\nPricing Models – Amazon Bedrock oﬀers two pricing models, on-demand and provisioned throughput. On-demand pricing allows you to use FMs on a pay-as-you-go basis without having to make any time-based term commitments. Provisioned throughput is primarily designed for large, consistent inference workloads that need guaranteed throughput in exchange for a term commitment. Here, you specify the number of model units of a particular FM to meet your application's performance requirements as deﬁned by the maximum number of input and output tokens processed per minute. For detailed pricing information, see Amazon Bedrock Pricing."}
```

4. Click **Create test event**
5. Click **Test**
6. Around 30 seconds later you should see a success message — click on **Details**

![Test Success](images/test-success.png)

7. Scroll down and maximize the **Log Output** and you will find an output similar to:

![Log Output](images/log-output.png)

Observe how the agent first plans its steps and selects the right tools for each task. After completing all steps, it delivers the final response to the user.

> Want to try a different tone? Just change "mythical" for another in the prompt and run the test again.

🎉 **Congratulations!** You've successfully created a Social Media Agent!

---

## Module 3 - Understanding Step Functions

### Code-Based vs Workflow-Based Agent Orchestration

When building AI agents, you have two main ways to control how they work:

**Code-based orchestration** — You write all the logic in your application code that handles the agent's thinking, tool use, and memory. This gives you full control and keeps everything simple since all the logic stays in one place. You can implement exactly what you need without learning new tools or services. However, you must build everything yourself — including error handling, state tracking, and monitoring. Additionally, using a compute service like Lambda might not be ideal since you're paying for compute time while the agent function sits idle waiting for tool responses.

**Workflow-based orchestration** — Rather than writing imperative code that dictates agent behavior, you define the agent's actions at each step and let the workflow engine manage the execution details. This declarative approach offers several key advantages:

- The workflow engine automatically manages state transitions
- Built-in error handling and retry mechanisms
- Efficient pause/resume while waiting for external responses (reduced compute costs)
- Improved scalability and simplified maintenance

> Many teams start with code-based orchestration and transition to workflow-based solutions as their agents become more sophisticated.

### Why Step Functions?

**AWS Step Functions** is the perfect solution for orchestrating interactions between models, tools, and users. It provides:

- A visual workflow service that simplifies complex request-response patterns
- Graphical workflow building and real-time execution monitoring
- Serverless — no infrastructure maintenance, version management, or scalability concerns
- Robust capabilities for sophisticated business logic and conditional branching
- Direct integration with over 11,000 AWS APIs across 200+ services, including Amazon Bedrock

### Create the Step Functions Workflow

In this section, you will build and run a Step Functions workflow to invoke the Amazon Bedrock API.

1. Open the **Step Functions console**
2. Create a State Machine using **Blank template**
3. Enter State machine name as `lab1-sfn-hello-world`
4. Leave the workflow type as **Standard** and click **Continue**
5. Explore the visual designer studio:
   - On the **left**, you see Actions, Flow and Patterns
   - In the **middle**, the graphical designer layout (drag and drop)
   - On the **right**, options to configure steps (switch between Code, Config, and Design tabs)
6. In the left panel, under **Actions** tab, search for `Converse`
7. Drag and drop **Amazon Bedrock Runtime Converse** to the designer canvas
8. In the right panel, under **Arguments & Output** tab, update the below code under the Arguments section:

```json
{
  "ModelId": "us.amazon.nova-lite-v1:0",
  "Messages": [
    {
      "Role": "user",
      "Content": [
        {
          "Text": "What is Amazon Bedrock Converse API?"
        }
      ]
    }
  ]
}
```

![stepfn-bedrock](images/stepfn-bedrock.png)

> ⚠️ **Important**: As you are creating the workflow, you will see a red banner at the top. Ignore it. It will disappear as you make progress and save the workflow.

9. Navigate to the top section and select **Config**. This page allows you to configure workflow name, IAM role, logging, etc.
10. Under **Permissions**, choose the execution role prefixed with `lab1-sfn-StepFunctionsExecutionRole`
11. Click **Create** on the top right

#### Run the Workflow

1. Click **Execute** on the top right
2. Do not change anything in the input and click **Start execution**

![stepfn-bedrock execution](images/stepfn-bedrock-execution.png)

3. Select the **Converse** task in the execution and explore the **State Output**

🎉 **Congratulations!** You have successfully invoked a Converse API in Amazon Bedrock using Step Functions.

---

## Module 4 - Agent Orchestration with AWS Step Functions

In this section you will explore how to use AWS Step Functions for agent orchestration and test the workflow. It recreates the Social Media Agent described in Module 2 leveraging the same tools, but using Step Functions for agent orchestration.

### Architecture Overview

This architecture creates a conversational agent that can iteratively process content through multiple specialized tools before delivering a final response, all while maintaining conversation context.

1. Navigate to **AWS Step Functions** in your AWS Console
2. Select the `lab1-social-media-agent-sfn` state machine
3. Click on **Edit** and you will see the below architecture:

![State Machine](images/state-machine.png)

The workflow operates as follows:

- The workflow begins at the **Invoke model** state, which calls Amazon Bedrock using a Lambda function to analyze user input and determine the next action
- Based on the model's response, the **Use tool?** state directs the flow either to return a final response via **Build response** or to the **Get tool** state to select an appropriate tool
- The state machine can invoke three specialized Lambda functions: **Content Summarizer**, **Tone Adapter**, and **Post Writer**
- After a tool executes, the **Add Tool Responses** state appends the result to the conversation history and loops back to **Invoke model** for further processing

> Explore the workflow by clicking on the states and checking its configuration in the right-hand panel.

### Testing the Step Function Agent

1. Click **Execute** in the top-right and provide the following input:

```json
{"prompt": "Please create a social media post using a mythical tone: This April, we announced Amazon Bedrock as part of a set of new tools for building with generative AI on AWS. Amazon Bedrock is a fully managed service that offers a choice of high-performing foundation models (FMs) from leading AI companies, including AI21 Labs, Anthropic, Cohere, Stability AI, and Amazon, along with a broad set of capabilities to build generative AI applications, simplifying the development while maintaining privacy and security.\n\nToday, I'm happy to announce that Amazon Bedrock is now generally available! I'm also excited to share that Meta's Llama 2 13B and 70B parameter models will soon be available on Amazon Bedrock.\n\nAmazon Bedrock's comprehensive capabilities help you experiment with a variety of top FMs, customize them privately with your data using techniques such as fine-tuning and retrieval-augmented generation (RAG), and create managed agents that perform complex business tasks—all without writing any code. Check out my previous posts to learn more about agents for Amazon Bedrock and how to connect FMs to your company's data sources.\n\nNote that some capabilities, such as agents for Amazon Bedrock, including knowledge bases, continue to be available in preview. I'll share more details on what capabilities continue to be available in preview towards the end of this blog post.\n\nSince Amazon Bedrock is serverless, you don't have to manage any infrastructure, and you can securely integrate and deploy generative AI capabilities into your applications using the AWS services you are already familiar with.\n\nAmazon Bedrock is integrated with Amazon CloudWatch and AWS CloudTrail to support your monitoring and governance needs. You can use CloudWatch to track usage metrics and build customized dashboards for audit purposes. With CloudTrail, you can monitor API activity and troubleshoot issues as you integrate other systems into your generative AI applications. Amazon Bedrock also allows you to build applications that are in compliance with the GDPR and you can use Amazon Bedrock to run sensitive workloads regulated under the U.S. Health Insurance Portability and Accountability Act (HIPAA).\n\nGet Started with Amazon Bedrock:\n    You can access available FMs in Amazon Bedrock through the AWS Management Console, AWS SDKs, and open-source frameworks such as LangChain.\n\nIn the Amazon Bedrock console, you can browse FMs and explore and load example use cases and prompts for each model. First, you need to enable access to the models. In the console, select Model access in the left navigation pane and enable the models you would like to access. Once model access is enabled, you can try out different models and inference configuration settings to find a model that fits your use case.\n\nData Privacy and Network Security:\n    With Amazon Bedrock, you are in control of your data, and all your inputs and customizations remain private to your AWS account. Your data, such as prompts, completions, and fine-tuned models, is not used for service improvement. Also, the data is never shared with third-party model providers.\n\nYour data remains in the Region where the API call is processed. All data is encrypted in transit with a minimum of TLS 1.2 encryption. Data at rest is encrypted with AES-256 using AWS KMS managed data encryption keys. You can also use your own keys (customer managed keys) to encrypt the data.\n\nYou can configure your AWS account and virtual private cloud (VPC) to use Amazon VPC endpoints (built on AWS PrivateLink) to securely connect to Amazon Bedrock over the AWS network. This allows for secure and private connectivity between your applications running in a VPC and Amazon Bedrock.\n\nGovernance and Monitoring:\n    Amazon Bedrock integrates with IAM to help you manage permissions for Amazon Bedrock. Such permissions include access to specific models, playground, or features within Amazon Bedrock. All AWS-managed service API activity, including Amazon Bedrock activity, is logged to CloudTrail within your account.\n\nAmazon Bedrock emits data points to CloudWatch using the AWS/Bedrock namespace to track common metrics such as InputTokenCount, OutputTokenCount, InvocationLatency, and (number of) Invocations. You can filter results and get statistics for a specific model by specifying the model ID dimension when you search for metrics. This near real-time insight helps you track usage and cost (input and output token count) and troubleshoot performance issues (invocation latency and number of invocations) as you start building generative AI applications with Amazon Bedrock.\n\nBilling and Pricing Models:\n    Here are a couple of things around billing and pricing models to keep in mind when using Amazon Bedrock:\n\nBilling – Text generation models are billed per processed input tokens and per generated output tokens. Text embedding models are billed per processed input tokens. Image generation models are billed per generated image.\n\nPricing Models – Amazon Bedrock oﬀers two pricing models, on-demand and provisioned throughput. On-demand pricing allows you to use FMs on a pay-as-you-go basis without having to make any time-based term commitments. Provisioned throughput is primarily designed for large, consistent inference workloads that need guaranteed throughput in exchange for a term commitment. Here, you specify the number of model units of a particular FM to meet your application's performance requirements as deﬁned by the maximum number of input and output tokens processed per minute. For detailed pricing information, see Amazon Bedrock Pricing."}
```

![Workflow Input Prompt](images/workflow-input-prompt.png)

2. Select **Start Execution** and wait until the execution is completed

![Workflow Completion](images/workflow-completion.png)

3. To verify the result, select the **Execution input and output** tab and check the **State Output**

![Workflow Output](images/workflow-output.png)

🎉 **Congratulations!** You have successfully added a new tool to the workflow and tested its use.
