"""
Comprehensive Google ADK Agent Development Sample
Demonstrates: agents, tools, memory, sessions, workflows, evaluation, and observability
"""
# ============================================================================
# PART 0: Quick Setup (Day 0 - Quick Start)
# ============================================================================
import os
from typing import Dict, Any, List
import json
from datetime import datetime

# Core ADK imports
from google.genai import Agent, LlmAgent, App
from google.genai.types import (
    Tool, FunctionTool, AgentTool,
    ToolContext, ResumabilityConfig
)
from google.genai.agents import (
    SequentialAgent, ParallelAgent, LoopAgent, BaseAgent
)
from vertexai.agent_engines import AdkApp
from vertexai.agent_engines.models import GeminiModel

from google.genai.runner import InMemoryRunner
from google.genai.tools import BuiltInCodeExecutor
from google.adk.tools import google_search
from google.genai.plugins import LoggingPlugin
from google.genai.memory import InMemoryMemoryService
from google.genai.sessions import (
    InMemorySessionService,
    DatabaseSessionService,
    EventsCompactionConfig,
    SlidingWindowCompactor
)
###### web interface: ######
#!adk create sample-agent --model gemini-2.5-flash-lite --api_key $GOOGLE_API_KEY
#!adk web --log_level DEBUG

###### evaluation: ######
#!adk eval sample-agent evalset.json

# ============================================================================
# PART 1: CUSTOM TOOLS (Day 2a - Agent Tools)
# ============================================================================

def calculate_statistics(data: List[float]) -> Dict[str, Any]:
    """
    Calculate basic statistics for a list of numbers.
    
    Args:
        data: List of numeric values
        
    Returns:
        Dictionary with status and statistical results
    """
    try:
        if not data:
            return {
                "status": "error",
                "error_message": "Empty data list provided"
            }
        
        return {
            "status": "success",
            "data": {
                "mean": sum(data) / len(data),
                "min": min(data),
                "max": max(data),
                "count": len(data)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to calculate statistics: {str(e)}"
        }


def check_budget(amount: float, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Check if an expense is within budget and request approval if needed.
    
    Args:
        amount: The expense amount to check
        tool_context: ADK tool context for user interaction
        
    Returns:
        Dictionary with approval status
    """
    try:
        budget_limit = 100.0
        
        if amount <= budget_limit:
            return {
                "status": "success",
                "approved": True,
                "message": f"Expense ${amount:.2f} is within budget limit"
            }
        else:
            # Request user confirmation for over-budget expenses
            confirmation = tool_context.request_confirmation(
                f"Expense ${amount:.2f} exceeds budget limit of ${budget_limit:.2f}. Approve?"
            )
            
            return {
                "status": "success",
                "approved": confirmation.approved,
                "message": "Expense approved" if confirmation.approved else "Expense denied"
            }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def store_session_data(key: str, value: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Store data in the session state for persistence across agent interactions.
    
    Args:
        key: The key to store data under
        value: The value to store
        tool_context: ADK tool context with session access
        
    Returns:
        Dictionary with storage status
    """
    try:
        tool_context.state[key] = value
        return {
            "status": "success",
            "message": f"Stored '{key}' in session state"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


# ============================================================================
# PART 2: AGENT ARCHITECTURES (Day 1b - Agent Architectures)
# ============================================================================

def create_basic_agent(api_key: str) -> LlmAgent:
    """Create a basic LLM agent with code execution capabilities."""
    agent = LlmAgent(
        name="basic_agent",
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        description="A basic agent that can execute Python code",
        instructions="You are a helpful assistant that can analyze data and execute code.",
        tools=[
            BuiltInCodeExecutor(),
            FunctionTool(func=calculate_statistics),
        ]
    )
    return agent


def create_workflow_agents(api_key: str) -> Dict[str, Agent]:
    """Create various workflow agent types: Sequential, Parallel, and Loop."""
    
    # Agent A: Data analyzer
    agent_a = LlmAgent(
        name="analyzer",
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        description="Analyzes data and provides insights",
        instructions="Analyze the given data and provide key insights."
    )
    
    # Agent B: Report generator
    agent_b = LlmAgent(
        name="reporter",
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        description="Generates reports from analysis",
        instructions="Create a formatted report from the analysis results."
    )
    
    # Sequential Agent (fixed pipeline)
    sequential_agent = SequentialAgent(
        name="sequential_workflow",
        description="Analyzes data then generates report",
        sub_agents=[agent_a, agent_b]
    )
    
    # Parallel Agent (concurrent pipeline)
    parallel_agent = ParallelAgent(
        name="parallel_workflow",
        description="Processes multiple tasks concurrently",
        sub_agents=[agent_a, agent_b]
    )
    
    # Loop Agent (refinement pipeline)
    def exit_loop(iteration: int, max_iterations: int = 3) -> bool:
        """Determine if the loop should exit."""
        return iteration >= max_iterations
    
    loop_agent = LoopAgent(
        name="loop_workflow",
        description="Refines output through iterations",
        agent=agent_a,
        exit_condition=exit_loop
    )
    
    return {
        "sequential": sequential_agent,
        "parallel": parallel_agent,
        "loop": loop_agent
    }


def create_hierarchical_agents(api_key: str) -> LlmAgent:
    """Create hierarchical agents with sub-agents (dynamic orchestration)."""
    
    # Specialist agent
    specialist_agent = LlmAgent(
        name="specialist",
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        description="Handles specialized tasks",
        instructions="You are a specialist in data processing."
    )
    
    # Root agent with sub-agents
    root_agent = LlmAgent(
        name="coordinator",
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        description="Coordinates and delegates tasks",
        instructions="Delegate complex tasks to specialist agents when needed.",
        sub_agents=[specialist_agent]
    )
    
    return root_agent


# ============================================================================
# PART 3: SESSIONS AND MEMORY (Day 3a/3b - Sessions & Memory)
# ============================================================================

def setup_session_service(use_database: bool = False) -> Any:
    """
    Set up session service for state persistence.
    
    Args:
        use_database: If True, use DatabaseSessionService; otherwise InMemorySessionService
    """
    if use_database:
        # For production: use database-backed sessions
        return DatabaseSessionService(
            db_url="sqlite:///agents.db",
            compaction_config=EventsCompactionConfig(
                compactor=SlidingWindowCompactor(window_size=50)
            )
        )
    else:
        # For prototyping: use in-memory sessions
        return InMemorySessionService(
            compaction_config=EventsCompactionConfig(
                compactor=SlidingWindowCompactor(window_size=50)
            )
        )


def setup_memory_service() -> InMemoryMemoryService:
    """Set up memory service for long-term memory storage."""
    return InMemoryMemoryService()


def create_memory_enabled_agent(api_key: str, memory_service: Any) -> LlmAgent:
    """Create an agent with memory capabilities."""
    from google.genai.tools import load_memory, preload_memory
    
    agent = LlmAgent(
        name="memory_agent",
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        description="An agent with long-term memory",
        instructions="Remember important information about users and past interactions.",
        tools=[
            load_memory,  # Reactive: loads memory when needed
            preload_memory  # Proactive: loads memory before every turn
        ]
    )
    
    return agent


# ============================================================================
# PART 4: OBSERVABILITY (Day 4a - Agent Observability)
# ============================================================================

class CustomLoggingPlugin:
    """Custom logging plugin for detailed agent observability."""
    
    def before_agent_callback(self, event):
        """Runs before agent starts processing."""
        print(f"[AGENT START] {event.agent_name} - {datetime.now()}")
    
    def after_agent_callback(self, event):
        """Runs after agent completes."""
        print(f"[AGENT END] {event.agent_name} - Duration: {event.duration}s")
    
    def before_tool_callback(self, event):
        """Runs before tool invocation."""
        print(f"[TOOL CALL] {event.tool_name} with args: {event.args}")
    
    def after_tool_callback(self, event):
        """Runs after tool completes."""
        print(f"[TOOL RESULT] {event.tool_name} - Status: {event.status}")
    
    def before_model_callback(self, event):
        """Runs before LLM call."""
        print(f"[LLM CALL] Model: {event.model_name}")
    
    def after_model_callback(self, event):
        """Runs after LLM responds."""
        print(f"[LLM RESPONSE] Tokens: {event.token_count}")
    
    def on_model_error_callback(self, event):
        """Handles errors."""
        print(f"[ERROR] {event.error_type}: {event.error_message}")


# ============================================================================
# PART 5: EVALUATION (Day 4b - Agent Evaluation)
# ============================================================================

def create_evaluation_dataset() -> Dict[str, Any]:
    """
    Create an evaluation dataset for testing agent performance.
    
    Returns:
        Dictionary containing test scenarios
    """
    return {
        "test_cases": [
            {
                "input": "Calculate the average of [10, 20, 30, 40]",
                "expected_output_contains": ["25", "average"],
                "description": "Basic statistics calculation"
            },
            {
                "input": "Generate a Python list of even numbers from 1 to 10",
                "expected_output_contains": ["[2, 4, 6, 8, 10]"],
                "description": "Code generation task"
            }
        ]
    }


def create_simulation_scenario() -> Dict[str, Any]:
    """
    Create a conversation simulation scenario for testing.
    
    Returns:
        Dictionary with simulation scenarios
    """
    return {
        "scenarios": [
            {
                "starting_prompt": "What can you do for me?",
                "conversation_plan": "Ask the agent to calculate statistics for a dataset, then ask for a visualization."
            },
            {
                "starting_prompt": "I need help with data analysis",
                "conversation_plan": "Provide sample data and ask for insights, then request a detailed report."
            }
        ]
    }


# ============================================================================
# PART 6: COMPLETE APPLICATION EXAMPLE
# ============================================================================

def create_production_agent(api_key: str) -> App:
    """
    Create a production-ready agent with all features:
    - Custom tools
    - Memory service
    - Session management
    - Observability
    - Resumability
    """
    
    # Setup services
    session_service = setup_session_service(use_database=False)
    memory_service = setup_memory_service()
    
    # Create agent with all features
    agent = LlmAgent(
        name="production_agent",
        model="gemini-2.5-flash-lite",
        api_key=api_key,
        description="A production-ready agent with full capabilities",
        instructions="""
        You are a helpful assistant with access to:
        - Code execution capabilities
        - Statistical analysis tools
        - Budget approval system
        - Session state management
        - Long-term memory
        
        Help users with their tasks efficiently and accurately.
        """,
        tools=[
            BuiltInCodeExecutor(),
            FunctionTool(func=calculate_statistics),
            FunctionTool(func=check_budget),
            FunctionTool(func=store_session_data)
        ]
    )
    
    # Wrap in App with resumability
    app = App(
        agent=agent,
        resumability_config=ResumabilityConfig(is_resumable=True)
    )
    
    # Create runner with plugins
    runner = InMemoryRunner(
        session_service=session_service,
        memory_service=memory_service,
        plugins=[
            LoggingPlugin(),
            CustomLoggingPlugin()
        ]
    )
    
    return app, runner


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution demonstrating all concepts."""
    
    # Setup (replace with your API key)
    api_key = os.getenv("GOOGLE_API_KEY", "your-api-key-here")
    
    print("=" * 80)
    print("Google ADK Agent Development - Comprehensive Sample")
    print("=" * 80)
    
    # 1. Basic Agent
    print("\n1. Creating Basic Agent...")
    basic_agent = create_basic_agent(api_key)
    print(f"   ✓ Created: {basic_agent.name}")
    
    # 2. Workflow Agents
    print("\n2. Creating Workflow Agents...")
    workflows = create_workflow_agents(api_key)
    for name, agent in workflows.items():
        print(f"   ✓ Created: {name} workflow")
    
    # 3. Hierarchical Agents
    print("\n3. Creating Hierarchical Agent System...")
    hierarchical = create_hierarchical_agents(api_key)
    print(f"   ✓ Created: {hierarchical.name}")
    
    # 4. Memory & Sessions
    print("\n4. Setting up Memory & Session Services...")
    session_svc = setup_session_service()
    memory_svc = setup_memory_service()
    print("   ✓ Services initialized")
    
    # 5. Production Agent
    print("\n5. Creating Production-Ready Agent...")
    app, runner = create_production_agent(api_key)
    print("   ✓ Production agent ready with all features")
    
    # 6. Evaluation Setup
    print("\n6. Creating Evaluation Assets...")
    eval_dataset = create_evaluation_dataset()
    simulation = create_simulation_scenario()
    print(f"   ✓ {len(eval_dataset['test_cases'])} test cases created")
    print(f"   ✓ {len(simulation['scenarios'])} simulation scenarios created")
    
    print("\n" + "=" * 80)
    print("Setup Complete! Key Commands:")
    print("=" * 80)
    print("  adk web --log_level DEBUG        # Launch web interface")
    print("  adk eval <agent> <evalset.json>  # Run evaluations")
    print("  adk create <name> --model ...    # Create new agent")
    print("=" * 80)
    
    # Example of running the agent
    print("\n7. Example Agent Execution:")
    print("   (Uncomment to run with valid API key)")
    
    # Uncomment to execute:
    # session = runner.create_session()
    # response = runner.run(
    #     app=app,
    #     session=session,
    #     user_input="Calculate statistics for [1, 2, 3, 4, 5]"
    # )
    # print(f"   Response: {response}")


if __name__ == "__main__":
    main()
