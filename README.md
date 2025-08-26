**Install the Python environment**
```
uv sync
```

**Run a Temporal server and create the namespace and Nexus endpoint**

```bash
temporal server start-dev
temporal operator namespace create --namespace a2a-namespace

temporal operator nexus endpoint create \
  --name a2a-nexus-endpoint \
  --target-namespace a2a-namespace \
  --target-task-queue a2a-handler-task-queue
```

**Run the examples**
```
$ uv run examples/send-message-from-workflow-to-nexus-op-that-responds-with-message.py

A2ACallerWorkflow.run(input=A2ACallerWorkflowInput(endpoint='a2a-nexus-endpoint'))
WorkflowNexusTransport.send_message(request={'configuration': {'acceptedOutputModes': [],
                   'blocking': True,
                   'historyLength': None,
                   'pushNotificationConfig': None},
 'message': {'contextId': None,
             'extensions': None,
             'kind': 'message',
             'messageId': '015e8994-5380-4d2c-a76b-f0a4a1cc08ca',
             'metadata': {'operation': 'greet', 'service': 'test-service'},
             'parts': [{'data': {'name': 'World'},
                        'kind': 'data',
                        'metadata': None}],
             'referenceTaskIds': None,
             'role': <Role.user: 'user'>,
             'taskId': None},
 'metadata': None})
TestServiceHandler.greet(message={'contextId': None,
 'extensions': None,
 'kind': 'message',
 'messageId': '015e8994-5380-4d2c-a76b-f0a4a1cc08ca',
 'metadata': {'operation': 'greet', 'service': 'test-service'},
 'parts': [{'data': {'name': 'World'}, 'kind': 'data', 'metadata': None}],
 'referenceTaskIds': None,
 'role': <Role.user: 'user'>,
 'taskId': None})
```

```
$ uv run examples/send-message-from-workflow-to-nexus-op-that-starts-workflow-and-responds-with-task.py

A2ACallerWorkflow.run(input=A2ACallerWorkflowInput(endpoint='a2a-nexus-endpoint'))
WorkflowNexusTransport.send_message(request={'configuration': {'acceptedOutputModes': [],
                   'blocking': True,
                   'historyLength': None,
                   'pushNotificationConfig': None},
 'message': {'contextId': None,
             'extensions': None,
             'kind': 'message',
             'messageId': '32ec7f48-f46c-4022-a26b-60a4c9f4e1d0',
             'metadata': {'operation': 'translate', 'service': 'test-service'},
             'parts': [{'kind': 'text',
                        'metadata': None,
                        'text': 'Hello, World'}],
             'referenceTaskIds': None,
             'role': <Role.user: 'user'>,
             'taskId': None},
 'metadata': None})
Received Task: <class 'a2a.types.Task'>, value: artifacts=None context_id='TODO' history=None id='eyJ0IjoxLCJucyI6ImEyYS1uYW1lc3BhY2UiLCJ3aWQiOiIwYWM3ZjBjYy01ODZkLTQyMjgtOTY2YS01Mjg5Y2U4ZWI0Y2IifQ' kind='task' metadata={'nexus_operation_handle': Future_6880[FINISHED] Future_1840[PENDING] Task[PENDING] fut_waiter = Future_0400[PENDING]) (False)} status=TaskStatus(message=None, state=<TaskState.working: 'working'>, timestamp=None)
Translation result: Bonjour, monde
```
