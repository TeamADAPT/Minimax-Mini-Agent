# Token Limit Configuration Update

## Changes Made

Updated the token limit for context compaction from 80,000 to 195,000 tokens to better utilize the MiniMax M2 API's maximum context window of 204,800 tokens.

## Files Modified

### 1. `/adapt/platform/novaops/mini_agent/agent.py`
```python
# Before:
token_limit: int = 80000,  # Summary triggered when tokens exceed this value

# After:
token_limit: int = 195000,  # Summary triggered when tokens exceed this value (set below 204800 API max)
```

### 2. `/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/agent.py`
```python
# Same change as above for the framework version
```

### 3. `/adapt/platform/novaops/mini_agent/config.py`
```python
class AgentConfig(BaseModel):
    """Agent configuration"""

    max_steps: int = 50
    workspace_dir: str = "./workspace"
    system_prompt_path: str = "system_prompt.md"
    token_limit: int = 195000  # Context compaction threshold (set below 204800 API max)
```

### 4. `/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/config.py`
```python
# Same change as above for the framework version
```

### 5. `/adapt/platform/novaops/mini_agent/cli.py`
```python
# Added token_limit parameter when creating Agent instance
agent = Agent(
    llm_client=llm_client,
    system_prompt=system_prompt,
    tools=tools,
    max_steps=config.agent.max_steps,
    workspace_dir=str(workspace_dir),
    token_limit=config.agent.token_limit,  # Now uses config value
)
```

### 6. `/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/cli.py`
```python
# Same change as above for the framework version
```

## Configuration

The token limit can now be configured in the config file:

**File**: `/adapt/platform/novaops/mini_agent/config/config.yaml`
```yaml
# Agent Configuration
max_steps: 2000000
workspace_dir: "./workspace"
system_prompt_path: "system_prompt.md"
token_limit: 195000  # Context compaction threshold (set below 204800 API max)
```

## Why 195,000?

- **API Maximum**: 204,800 tokens
- **Safety Buffer**: 9,800 tokens (≈ 4.8% buffer)
- **Compaction Threshold**: 195,000 tokens

This buffer ensures:
1. We never exceed the API's hard limit
2. Room for the system prompt and tool responses
3. Safe margin for token estimation inaccuracies

## Benefits

With the increased token limit:
- **Longer conversations** before compaction/summarization triggers
- **More context retention** across multi-turn interactions
- **Better performance** on complex tasks requiring extensive history
- **Reduced frequency** of context summarization

## Testing

To verify the new token limit is active:

```bash
cd /adapt/platform/novaops
mini-agent --workspace /path/to/test/dir

# In the agent CLI, use:
/stats  # Shows current token usage and limit
```

You should see the token limit displayed as 195,000 in the stats output.

## Compatibility

- **Backwards Compatible**: Existing configs without `token_limit` will use the new default of 195,000
- **Override Supported**: Users can still set custom values in their config.yaml
- **Session Files**: Existing session files are compatible with the new limit
