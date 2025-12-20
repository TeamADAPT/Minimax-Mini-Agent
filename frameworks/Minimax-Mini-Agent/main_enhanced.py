#!/usr/bin/env python3
"""
Enhanced Mini Agent Runner

This script demonstrates all enhanced features of Mini Agent:
- All basic tools (file operations, bash)
- Session notes for persistent memory
- MCP tools (web search, knowledge graphs)
- Claude Skills integration
- Pause/Interject functionality
- All configuration enhancements
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for development mode
sys.path.insert(0, str(Path(__file__).parent))

from mini_agent import LLMClient, LLMProvider
from mini_agent.agent import Agent
from mini_agent.config import Config
from mini_agent.tools import BashTool, EditTool, ReadTool, WriteTool
from mini_agent.tools.bash_tool import BashKillTool, BashOutputTool
from mini_agent.tools.mcp_loader import cleanup_mcp_connections, load_mcp_tools_async
from mini_agent.tools.note_tool import RecallNoteTool, SessionNoteTool
from mini_agent.tools.skill_tool import create_skill_tools


def check_configuration():
    """Check if configuration is set up correctly."""
    print("🔍 Checking configuration...")

    config_path = Path("mini_agent/config/config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found")
        print("   Please run: cp mini_agent/config/config-example.yaml mini_agent/config/config.yaml")
        return False

    try:
        config = Config.from_yaml(config_path)
        if not config.llm.api_key or config.llm.api_key.startswith("YOUR_"):
            print("❌ API key not configured in config.yaml")
            print("   Please add your MiniMax API key to mini_agent/config/config.yaml")
            return False

        print(f"✅ API Key configured")
        print(f"✅ API Base: {config.llm.api_base}")
        print(f"✅ Model: {config.llm.model}")
        print(f"✅ Max Steps: {config.agent.max_steps}")
        return True
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False


async def run_enhanced_agent():
    """Run the enhanced agent with all features enabled."""
    print("\n" + "=" * 80)
    print("🚀 Mini Agent - Enhanced Version with All Features")
    print("=" * 80)
    print("\nFeatures enabled:")
    print("✅ All basic tools (Read, Write, Edit, Bash)")
    print("✅ Session notes (persistent memory)")
    print("✅ MCP tools (web search, knowledge graphs)")
    print("✅ Claude Skills (15+ professional skills)")
    print("✅ Pause/Interject functionality (Ctrl+C during execution)")
    print("✅ High max_steps (2000000)")
    print("=" * 80)

    if not check_configuration():
        print("\n❌ Configuration check failed. Please fix the issues above.")
        return

    config_path = Path("mini_agent/config/config.yaml")
    config = Config.from_yaml(config_path)

    # Create workspace
    workspace_dir = Path(config.agent.workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Workspace: {workspace_dir}")

    # Initialize all tools
    tools = []

    # Basic tools
    tools.extend([
        ReadTool(workspace_dir=str(workspace_dir)),
        WriteTool(workspace_dir=str(workspace_dir)),
        EditTool(workspace_dir=str(workspace_dir)),
    ])
    print("✅ Loaded basic file tools")

    # Bash tools
    tools.extend([
        BashTool(),
        BashOutputTool(),
        BashKillTool(),
    ])
    print("✅ Loaded bash tools")

    # Session note tools
    memory_file = workspace_dir / ".agent_memory.json"
    tools.extend([
        SessionNoteTool(memory_file=str(memory_file)),
        RecallNoteTool(memory_file=str(memory_file)),
    ])
    print("✅ Loaded session note tools")

    # MCP tools
    mcp_config_path = Path("mini_agent/config/mcp.json")
    if mcp_config_path.exists():
        try:
            mcp_tools = await load_mcp_tools_async(str(mcp_config_path))
            if mcp_tools:
                tools.extend(mcp_tools)
                print(f"✅ Loaded {len(mcp_tools)} MCP tools")
            else:
                print("⚠️  No MCP tools configured or all disabled")
        except Exception as e:
            print(f"⚠️  Failed to load MCP tools: {e}")
    else:
        print("⚠️  MCP config file not found")

    # Claude Skills
    skills_dir = Path("mini_agent/skills")
    if skills_dir.exists():
        try:
            skill_tools, skill_loader = create_skill_tools(str(skills_dir))
            if skill_tools:
                tools.extend(skill_tools)
                print(f"✅ Loaded Claude Skills")
            else:
                print("⚠️  No skills found")
        except Exception as e:
            print(f"⚠️  Failed to load skills: {e}")
    else:
        print("⚠️  Skills directory not found")

    print(f"\n📊 Total tools loaded: {len(tools)}")

    # Initialize LLM client
    provider = LLMProvider.ANTHROPIC if config.llm.provider.lower() == "anthropic" else LLMProvider.OPENAI
    llm_client = LLMClient(
        api_key=config.llm.api_key,
        provider=provider,
        api_base=config.llm.api_base,
        model=config.llm.model,
    )
    print(f"✅ Initialized LLM client ({provider.value})")

    # Load system prompt
    system_prompt_path = Path("mini_agent/config/system_prompt.md")
    if system_prompt_path.exists():
        system_prompt = system_prompt_path.read_text(encoding="utf-8")
        print("✅ Loaded system prompt")
    else:
        system_prompt = "You are Mini-Agent, an intelligent assistant that can help users complete various tasks."
        print("⚠️  System prompt not found, using default")

    # Add session memory instructions
    note_instructions = """

IMPORTANT - Session Memory:
You have record_note and recall_notes tools. Use them to:
- Save important facts, decisions, and context
- Recall previous information across sessions
"""
    system_prompt += note_instructions

    # Create agent
    agent = Agent(
        llm_client=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        max_steps=config.agent.max_steps,
        workspace_dir=str(workspace_dir),
    )
    print(f"✅ Created agent with max_steps={config.agent.max_steps}")

    print("\n" + "=" * 80)
    print("🎉 Enhanced agent is ready!")
    print("=" * 80)
    print("\n💡 Quick start tasks you can try:")
    print("1. Create a Python script with error handling")
    print("2. Search for information and save to a file")
    print("3. Generate a PDF report about a topic")
    print("4. Create a web application with Flask")
    print("5. Build a knowledge base and query it")
    print("\n📌 Press Ctrl+C during task execution to pause and interject")
    print("   with new instructions or change direction.")
    print("=" * 80)

    # Simple interactive mode
    while True:
        print()
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print("\n👋 Goodbye!")
            break

        if user_input == "/help":
            print("\nAvailable commands:")
            print("  /help     - Show this help")
            print("  /clear    - Clear conversation history")
            print("  /exit     - Exit")
            print("\nType a task or question to start!")
            continue

        if user_input == "/clear":
            agent.messages = [agent.messages[0]]  # Keep system prompt
            print("\n✅ Conversation history cleared")
            continue

        print(f"\n🤖 Agent is working... (Press Ctrl+C to pause)")
        agent.add_user_message(user_input)

        try:
            result = await agent.run()
            print(f"\n✅ Agent response: {result}\n")
        except KeyboardInterrupt:
            print("\n\n⏸️  Agent paused. Type /continue to resume or enter new instructions.")
            continue
        except Exception as e:
            print(f"\n❌ Error: {e}")

    # Cleanup
    await cleanup_mcp_connections()


def main():
    """Main entry point."""
    print("Mini Agent - Enhanced Runner")
    print("=" * 80)

    try:
        asyncio.run(run_enhanced_agent())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nCleaning up...")


if __name__ == "__main__":
    main()
