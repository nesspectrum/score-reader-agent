import os
import asyncio
import argparse
import warnings
import sys
from io import StringIO
from contextlib import contextmanager
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.apps.app import App, ResumabilityConfig
from agents.music_assistant import MusicAssistantAgent
from agents.library_agent import LibraryAgent
from tools.library_manager import LibraryManager

# Suppress warnings about function_call parts in responses
warnings.filterwarnings('ignore', message='.*non-text parts.*function_call.*')
warnings.filterwarnings('ignore', message='.*returning concatenated text result.*')

# Context manager to filter stderr warnings from google.genai
@contextmanager
def suppress_genai_warnings():
    """Suppress warnings from google.genai about function_call parts."""
    original_stderr = sys.stderr
    filtered_stderr = StringIO()
    
    class FilteredStderr:
        def __init__(self, original):
            self.original = original
            self.buffer = []
        
        def write(self, text):
            # Filter out the specific warning messages
            if 'Warning: there are non-text parts in the response' in text:
                return
            if 'returning concatenated text result from text parts' in text:
                return
            if 'Check the full candidates.content.parts accessor' in text:
                return
            # Write everything else to original stderr
            self.original.write(text)
        
        def flush(self):
            self.original.flush()
        
        def __getattr__(self, name):
            return getattr(self.original, name)
    
    sys.stderr = FilteredStderr(original_stderr)
    try:
        yield
    finally:
        sys.stderr = original_stderr

# Load environment variables
load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Music Assistant Agent")
    parser.add_argument("query", nargs="?", help="Initial query for the assistant")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--file", "-f", help="Path to image/PDF file to upload")
    args = parser.parse_args()

    # Initialize services
    library_manager = LibraryManager()
    library_agent = LibraryAgent(library_manager=library_manager, output_key="response")
    memory_service = InMemoryMemoryService()
    root_agent = MusicAssistantAgent(library_agent=library_agent)
    session_service = InMemorySessionService()
    
    # Create App wrapper with correct name to avoid app name mismatch warning
    music_assistant = App(
        name="MusicAssistant",
        root_agent=root_agent,
        resumability_config=ResumabilityConfig(is_resumable=True),
    )
    
    # Create Runner with App wrapper
    runner = Runner(
        app=music_assistant,
        session_service=session_service,
        memory_service=memory_service
    )

    print("🎵 Music Assistant Initialized")
    print("Ask me to find a piece of music based on composer, piece name, or upload a sheet to digitize.")
    if args.interactive:
        print("In interactive mode, type 'upload <filepath>' to upload an image.")

    if args.interactive:
        session_id = "interactive-session"
        user_id = "default-user"
        
        # Create session
        await session_service.create_session(app_name="MusicAssistant", session_id=session_id, user_id=user_id)
        
        while True:
            try:
                user_input = input("\nUser > ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                # Check if user wants to upload a file
                file_path = None
                if user_input.lower().startswith('upload '):
                    file_path = user_input[7:].strip()
                    user_input = f"Please convert this music sheet image to MusicXML. File path: {file_path}"
                
                # Use Runner's run_async method with proper parameters
                from google.genai import types
                import os
                
                # Build message parts
                parts = [types.Part(text=user_input)]
                
                # Add file if provided
                if file_path and os.path.exists(file_path):
                    print(f"📎 Uploading file: {file_path}")
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Determine MIME type
                    mime_type = "image/jpeg"
                    if file_path.lower().endswith('.png'):
                        mime_type = "image/png"
                    elif file_path.lower().endswith('.pdf'):
                        mime_type = "application/pdf"
                    
                    # Add inline data part
                    import base64
                    parts.append(types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=base64.b64encode(file_data).decode('utf-8')
                        )
                    ))
                
                print("\nAssistant > ", end="", flush=True)
                with suppress_genai_warnings():
                    async for event in runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=types.Content(parts=parts)
                    ):
                        # Print the event content - only text parts, ignore function calls
                        if hasattr(event, 'content') and event.content:
                            if hasattr(event.content, 'parts') and event.content.parts:
                                for part in event.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        print(part.text, end="", flush=True)
                                    # Skip function_call parts silently
                print()  # New line after response
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()
    
    elif args.query or args.file:
        try:
            # Use Runner's run_async method with proper parameters
            from google.genai import types
            import os
            import base64
            
            session_id = "single-query-session"
            user_id = "default-user"
            
            # Create session
            await session_service.create_session(app_name="MusicAssistant", session_id=session_id, user_id=user_id)
            
            # Build message
            query_text = args.query if args.query else "I'm uploading a music sheet. Please convert it to MusicXML."
            parts = [types.Part(text=query_text)]
            
            # Add file if provided
            if args.file:
                if not os.path.exists(args.file):
                    print(f"Error: File not found: {args.file}")
                    return
                
                print(f"📎 Uploading file: {args.file}")
                with open(args.file, 'rb') as f:
                    file_data = f.read()
                
                # Determine MIME type
                mime_type = "image/jpeg"
                if args.file.lower().endswith('.png'):
                    mime_type = "image/png"
                elif args.file.lower().endswith('.pdf'):
                    mime_type = "application/pdf"
                
                # Add inline data part
                parts.append(types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=base64.b64encode(file_data).decode('utf-8')
                    )
                ))
            
            print("\nAssistant > ", end="", flush=True)
            with suppress_genai_warnings():
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=types.Content(parts=parts)
                ):
                    # Print the event content - only text parts, ignore function calls
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts') and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    print(part.text, end="", flush=True)
                                # Skip function_call parts silently
            print()  # New line after response
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
