# Disable LiteLLM logging before any imports
import os

os.environ["LITELLM_LOG"] = "CRITICAL"

import asyncio
import pprint
import uuid
from dataclasses import dataclass
from datetime import timedelta

from a2a.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
    Task,
    TextPart,
)
from a2a.utils import new_agent_text_message
from nexusrpc import Operation, service
from nexusrpc.handler import service_handler
from pydantic import BaseModel
from temporalio import nexus, workflow
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from nexus_a2a_python.workflow_transport import create_workflow_nexus_transport

with workflow.unsafe.imports_passed_through():
    from nexus_a2a_python import activities

NEXUS_ENDPOINT_NAME = "a2a-nexus-endpoint"
NAMESPACE = "a2a-namespace"
TASK_QUEUE = "a2a-handler-task-queue"


###################################################################################################
@service(name="test-service")
class TestService:
    translate: Operation[Message, Message]


@workflow.defn(sandboxed=False)
class TranslateWorkflow:
    @workflow.run
    async def run(self, input: Message) -> Message:
        assert isinstance(input.parts[0].root, TextPart)
        to_translate = input.parts[0].root.text
        prompt = f"Translate the following text to French: {to_translate}"
        translated = await workflow.execute_activity(
            activities.llm, prompt, schedule_to_close_timeout=timedelta(seconds=60)
        )
        return new_agent_text_message(translated)


@service_handler(service=TestService)
class TestServiceHandler:
    @nexus.workflow_run_operation
    async def translate(
        self, ctx: nexus.WorkflowRunOperationContext, message: Message
    ) -> nexus.WorkflowHandle[Message]:
        return await ctx.start_workflow(
            TranslateWorkflow.run,
            message,
            id=str(uuid.uuid4()),
        )


agent_card = AgentCard(
    name="French Translation Agent",
    description="Translate text to French",
    url=NEXUS_ENDPOINT_NAME,
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(push_notifications=True),
    additional_interfaces=[
        AgentInterface(
            url=NEXUS_ENDPOINT_NAME,
            transport="temporal-workflow-nexus-transport",
        )
    ],
    skills=[
        AgentSkill(
            id="translate",
            name="translate",
            description="Translate text to French",
            input_modes=["text"],
            output_modes=["text"],
            tags=["translation", "french"],
        ),
    ],
    supports_authenticated_extended_card=True,
)

###################################################################################################


class MyInput(BaseModel):
    name: str


class MyOutput(BaseModel):
    message: str


@dataclass
class A2ACallerWorkflowInput:
    endpoint: str


# sandbox disabled due to use of ThreadLocal by sniffio
# TODO: make this unnecessary
@workflow.defn(sandboxed=False)
class A2ACallerWorkflow:
    @workflow.run
    async def run(self, input: A2ACallerWorkflowInput) -> list[Message]:
        print(f"A2ACallerWorkflow.run(input={pprint.pformat(input)})")

        transport_name = "temporal-workflow-nexus-transport"
        config = ClientConfig(supported_transports=[transport_name])
        factory = ClientFactory(config)
        factory.register(transport_name, create_workflow_nexus_transport)
        client = factory.create(agent_card)
        request_message = Message(
            message_id=str(uuid.uuid4()),
            parts=[Part(root=TextPart(text="Hello, World"))],
            role=Role.user,
            metadata={"service": "test-service", "operation": "translate"},
        )
        response_messages = []
        async for message in client.send_message(request_message):
            # TODO: why is message a tuple? (task, None)
            task: Task
            if (
                isinstance(message, tuple)
                and len(message) > 0
                and isinstance(message[0], Task)
            ):
                task = message[0]
            elif isinstance(message, Task):
                task = message
            else:
                print(f"Warning: Unexpected message type: {type(message)}")
                continue
            print(f"Received Task: {type(task)}, value: {task}")
            assert task.metadata
            operation_handle = task.metadata["nexus_operation_handle"]
            response_messages.append(await operation_handle)
        return response_messages


async def main() -> None:
    client = await Client.connect(
        target_host="localhost:7233",
        namespace=NAMESPACE,
        data_converter=pydantic_data_converter,
    )

    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[A2ACallerWorkflow, TranslateWorkflow],
        activities=[activities.llm],
        nexus_service_handlers=[TestServiceHandler()],
    ):
        result = await client.execute_workflow(
            A2ACallerWorkflow.run,
            arg=A2ACallerWorkflowInput(endpoint=NEXUS_ENDPOINT_NAME),
            id=str(uuid.uuid4()),
            task_queue=TASK_QUEUE,
        )
        assert len(result) == 1
        [message] = result
        assert isinstance(message, Message)
        assert len(message.parts) == 1
        [part] = message.parts
        assert isinstance(part.root, TextPart)
        print(f"Translation result: {part.root.text}")


if __name__ == "__main__":
    asyncio.run(main())
