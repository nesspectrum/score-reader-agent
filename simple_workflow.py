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
from google.adk.tools import VertexAiSearchTool


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

# Setup services
session_service = setup_session_service(use_database=False)
memory_service = setup_memory_service()

# Create agent with all features
agent = LlmAgent(
    name="Music Assistant",
    model="gemini-2.5-flash-lite",
    api_key=api_key,
    description="You are a helpful assistant that reads music sheets, convert them to MusicXML, and recite it for your user.",
    instructions="""
    You are a helpful assistant with access to:
    - image to musicxml conversion tool
    - musicxml to json conversion tool
    - text to speech conversion tool
    - json to speech conversion tool
    - search memory tool
    - google search tool
    - session state management tool
    - long-term memory tool
    
    Help users with their tasks efficiently and accurately.
    """,
    tools=[
        FunctionTool(func=convert_image_to_musicxml),
        FunctionTool(func=convert_musicxml_to_json),
        FunctionTool(func=convert_text_to_speech),
        FunctionTool(func=convert_json_to_speech),
        FunctionTool(func=search_memory),
        FunctionTool(func=google_search),
    ])
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

