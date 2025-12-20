x@x:/adapt$ cd /adapt/platform/novaops
x@x:/adapt/platform/novaops$ mm -resume
usage: mini-agent [-h] [--workspace WORKSPACE] [--version] [--resume]
mini-agent: error: unrecognized arguments: -esume
x@x:/adapt/platform/novaops$ mm --resume
🔐 Using API key from secrets file: /adapt/secrets/m2.env
🔍 Looking for saved session in workspace: /adapt/platform/novaops
🔄 Resuming last global session: novaops
✅ Loaded 2 messages from global session

✅ LLM retry mechanism enabled (max 3 retries)
✅ Loaded Bash tool
✅ Loaded Bash Output tool
✅ Loaded Bash Kill tool
Loading Claude Skills...
✅ Discovered 15 Claude Skills
✅ Loaded Skill tool (get_skill)
Loading MCP tools...
Installed 55 packages in 121ms
None of PyTorch, TensorFlow >= 2.0, or Flax have been found. Models won't be available and only tokenizers, configuration and file/data utilities can be used.
2025-12-18 23:08:25,408 - minimax_search - INFO - Starting MiniMax Search MCP Server...
2025-12-18 23:08:25,409 - minimax_search - INFO - MiniMax Search MCP Server initialized
2025-12-18 23:08:25,475 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest
✓ Connected to MCP server 'minimax_search' - loaded 2 tools
  - search: Web search in parallel. The parameter is a list of queries. ...
  - browse: Explore specific information in a list of urls. The paramete...
Knowledge Graph MCP Server running on stdio
✓ Connected to MCP server 'memory' - loaded 9 tools
  - create_entities: Create multiple new entities in the knowledge graph...
  - create_relations: Create multiple new relations between entities in the knowle...
  - add_observations: Add new observations to existing entities in the knowledge g...
  - delete_entities: Delete multiple entities and their associated relations from...
  - delete_observations: Delete specific observations from entities in the knowledge ...
  - delete_relations: Delete multiple relations from the knowledge graph...
  - read_graph: Read the entire knowledge graph...
  - search_nodes: Search for nodes in the knowledge graph based on a query...
  - open_nodes: Open specific nodes in the knowledge graph by their names...

Total MCP tools loaded: 11
✅ Loaded 11 MCP tools (from: /adapt/platform/novaops/mini_agent/config/mcp.json)

✅ Loaded file operation tools (workspace: /adapt/platform/novaops)
✅ Loaded session note tool
✅ Loaded system prompt (from: /adapt/platform/novaops/mini_agent/config/system_prompt.md)
🔄 Hotloaded rules from: /adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/config/TeamADAPT_Rules.md
📋 Loaded 9 rules/protocols sections
✅ Injected 15 skills metadata into system prompt
an error occurred during closing of asynchronous generator <async_generator object stdio_client at 0x7f598afae650>
asyncgen: <async_generator object stdio_client at 0x7f598afae650>
  + Exception Group Traceback (most recent call last):
  |   File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 781, in __aexit__
  |     raise BaseExceptionGroup(
  |         "unhandled errors in a TaskGroup", self._exceptions
  |     ) from None
  | BaseExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/mcp/client/stdio/__init__.py", line 189, in stdio_client
    |     yield read_stream, write_stream
    | GeneratorExit
    +------------------------------------

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/mcp/client/stdio/__init__.py", line 183, in stdio_client
    anyio.create_task_group() as tg,
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 787, in __aexit__
    if self.cancel_scope.__exit__(type(exc), exc, exc.__traceback__):
       ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 459, in __exit__
    raise RuntimeError(
    ...<2 lines>...
    )
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
an error occurred during closing of asynchronous generator <async_generator object stdio_client at 0x7f598b05cd60>
asyncgen: <async_generator object stdio_client at 0x7f598b05cd60>
  + Exception Group Traceback (most recent call last):
  |   File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 781, in __aexit__
  |     raise BaseExceptionGroup(
  |         "unhandled errors in a TaskGroup", self._exceptions
  |     ) from None
  | BaseExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/mcp/client/stdio/__init__.py", line 189, in stdio_client
    |     yield read_stream, write_stream
    | GeneratorExit
    +------------------------------------

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/mcp/client/stdio/__init__.py", line 183, in stdio_client
    anyio.create_task_group() as tg,
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 787, in __aexit__
    if self.cancel_scope.__exit__(type(exc), exc, exc.__traceback__):
       ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/x/.local/share/uv/tools/mini-agent/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 459, in __exit__
    raise RuntimeError(
    ...<2 lines>...
    )
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
Traceback (most recent call last):
  File "/home/x/.local/bin/mini-agent", line 10, in <module>
    sys.exit(main())
             ~~~~^^
  File "/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/cli.py", line 873, in main
    asyncio.run(run_agent(workspace_dir))
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/x/.local/share/uv/python/cpython-3.13.9-linux-x86_64-gnu/lib/python3.13/asyncio/runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "/home/x/.local/share/uv/python/cpython-3.13.9-linux-x86_64-gnu/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/home/x/.local/share/uv/python/cpython-3.13.9-linux-x86_64-gnu/lib/python3.13/asyncio/base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/cli.py", line 549, in run_agent
    agent = Agent(
        llm_client=llm_client,
    ...<4 lines>...
        messages=initial_messages,
    )
TypeError: Agent.__init__() got an unexpected keyword argument 'messages'
x@x:/adapt/platform/novaops$ 

