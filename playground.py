# Load environment variables
from dotenv import load_dotenv
import os
import asyncio
import base64
import uuid
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.apps.app import App, ResumabilityConfig
from google.adk.agents import Agent
from google.genai import types

from agents.music_assistant import MusicAssistantAgent
from agents.library_agent import LibraryAgent

load_dotenv()

# Initialize services
library = LibraryAgent()
memory_service = InMemoryMemoryService()
agent = MusicAssistantAgent(library_agent=library)
session_service = InMemorySessionService()

# Create App with resumability
music_assistant_app = App(
    name="MusicAssistant",
    root_agent=agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)

# Create Runner
music_assistant_runner = Runner(
    app=music_assistant_app,
    session_service=session_service,
    memory_service=memory_service
)

async def run_music_workflow(query: str):
    """
    Runs a music search and, if music is not found, handles user validation of the generated MusicXML file.
    
    Args:
        query: User's music request (e.g. "find Bach Preludes" or "convert file.png to MusicXML")
    """
    print(f"\n{'='*60}")
    print(f"User > {query}\n")

    # Generate unique session ID
    session_id = f"music_{uuid.uuid4().hex[:8]}"
    user_id = "default-user"
    app_name = "MusicAssistant"

    # Create session
    await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    query_content = types.Content(parts=[types.Part(text=query)])
    response_events = []
    found_music = False
    musicxml_path = None

    # Step 1: Query the Music Assistant
    print("Assistant > ", end="", flush=True)
    async for event in music_assistant_runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=query_content
    ):
        response_events.append(event)
        # Print and parse agent's response
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(part.text, end="", flush=True)
                    # Very naive detection - refine if possible:
                    if "Found" in part.text or "Results:" in part.text or "found" in part.text.lower():
                        found_music = True
    print()  # New line after response

    # Step 2: If music was not found, prompt for MusicXML validation
    if not found_music and musicxml_path:
        print("\nMusic not found in the database.")
        print(f"Generated MusicXML file at: {musicxml_path}")
        # Prompt user for validation
        user_decision = input("Would you like to validate and accept this MusicXML file? (y/n): ").strip().lower()
        if user_decision == "y":
            print("✅ MusicXML file validated and accepted by user.")
            # You might want to proceed to add it to the library or next step here.
        else:
            print("❌ MusicXML file rejected by user.")
    elif not found_music:
        print("\nMusic not found and no MusicXML file generated.")
    print(f"{'='*60}\n")

async def main():
    """Main entry point"""
    await run_music_workflow("find Bach Prelude in C Major")

if __name__ == "__main__":
    asyncio.run(main())