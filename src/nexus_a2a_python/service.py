import pprint

from a2a.types import (
    DataPart,
    Message,
)
from a2a.utils import new_agent_text_message
from nexusrpc import Operation, service
from nexusrpc.handler import StartOperationContext, service_handler, sync_operation
from pydantic import BaseModel

NEXUS_ENDPOINT_NAME = "a2a-nexus-endpoint"
NAMESPACE = "a2a-namespace"
TASK_QUEUE = "a2a-handler-task-queue"


class MyInput(BaseModel):
    name: str


@service(name="test-service")
class TestService:
    greet: Operation[Message, Message]


@service_handler(service=TestService)
class TestServiceHandler:
    @sync_operation
    async def greet(self, ctx: StartOperationContext, message: Message) -> Message:
        """
        This is a test operation.
        """
        print(
            f"🌈 TestServiceHandler.greet(message={pprint.pformat(message.model_dump())})"
        )
        assert len(message.parts) == 1
        [part] = message.parts
        assert isinstance(part.root, DataPart)
        return new_agent_text_message(f"Hello, {part.root.data['name']}")
