# Running Workshop in Your Own AWS Account

> **Important:** Self-hosting the workshop will incur costs related to the provisioned and used resources. Please follow the clean up instructions after finishing the workshop to avoid unnecessary costs.

This section provides instructions for participants who are running this workshop in their own AWS account rather than in an AWS-provided event environment.

## Prerequisites

Before you begin, ensure you have:

- An AWS account with administrative permissions
- Access to the AWS Management Console
- Familiarity with AWS CloudFormation

## Deployment Steps

1. Click the link to launch the CloudFormation stack in the **US West 2 (Oregon)** region
2. On the CloudFormation console:
   - Confirm that you're in the US West 2 (Oregon) region
   - The template URL should be pre-populated
   - Click **Next**
3. **Stack details:**
   - Stack name: `agentic-ai-workshop` (or choose your preferred name)
   - Review the parameters but don't change anything
   - Click **Next**
4. **Configure stack options:**
   - Leave the default settings
   - Check the acknowledgment box for IAM resource creation
   - Click **Next**
5. Click **Create stack**
6. The stack creation will take approximately 5-15 minutes. You can monitor the progress in the CloudFormation console.

## Next Steps

After successfully deploying the CloudFormation stack, go to **Introduction to Agentic AI** and proceed with the workshop.

---

# Clean Up

> Only clean up if you are running this on your own AWS account. If you are running this workshop at an AWS event, the resources will be automatically destroyed when the workshop ends.

In this section, we'll clean up all the resources created during the workshop to ensure you don't incur any unexpected charges.

## CloudFormation Stacks

The easiest way to clean up most resources is to delete the CloudFormation stacks:

1. Open the AWS CloudFormation console
2. Delete the following stacks in this order:
   - `agents-bedrock` (if you deployed it)
   - `weather-agent` (if you deployed it)
   - `bedrock-workshop-resources`
3. Open the Amazon Bedrock console
4. Navigate to **Agents** and delete any agents you created

If you encounter any issues during clean up, please refer to the specific service documentation or contact AWS Support.
