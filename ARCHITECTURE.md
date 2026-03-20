This repo implements an end-to-end customer service copilot agent with human in the loop. Basically, this provides draft messages for the customer service people to quickly approve or modify, and send to the customer. 

The core value of the agent is to integrate with the data system of the company and autonomously retrieve the related information and parse to the best effort draft reply message.

The system contains the following components.
- A backend service to handle in coming service calls, and run the agent loop to generate the draft messages.
- A CLI that tests the backend service.
- A frontend UI that customer service human uses to approve and modify the messages. (To be built)


Functional features for the backend:
- Receive testing customer messages from the CLI, and return drafted messages.
- Integrate with the company internal data system. The access of the data is internally encapsulated into tool calls for the LLMs.
  - Starting with readonly local csv files.
  - Support popular database and MCPs in the future (to be build)
- Support configurable natural language business desciptions and instructions. For each supported company or business, the agent loop calls LLM APIs using the configured information.
- Integration with real world chat applications as a customer service account. Hook on the customer service account on the chat app, and generate a draft message for each in-coming message. (TO BE built)

Non-functional features for the backend:
- Save the LLM calling logs in a folder for debugging purposes.
- A debugging and evaluation portal will be built to browse and replay the LLM logs. (to be built)

Implementations:
- The backend service is implemented in FastAPI python.
- The service is designed to be local runable for now.
- Discuss the format of the LLM logging and update this section.