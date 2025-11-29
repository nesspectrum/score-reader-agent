import os
import argparse
import asyncio
import warnings
import sys
from io import StringIO
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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


async def run_music_assistant(args):
    """Run the Music Assistant Agent (interactive chat mode)."""
    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.adk.memory import InMemoryMemoryService
    from google.adk.apps.app import App, ResumabilityConfig
    from agents.music_assistant import MusicAssistantAgent
    from agents.library_agent import LibraryAgent
    from tools.library_manager import LibraryManager
    from google.genai import types
    import base64

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
        print("Use --interactive for chat mode, or provide a query/--file for single query mode.")


async def run_extraction_workflow(args):
    """Run the extraction workflow with audio playback (legacy mode)."""
    from agents.extraction_agent import ExtractionAgent
    from tools.library_manager import LibraryManager as LibraryAgent
    from tools.correction_tool import CorrectionTool
    from tools.audio_tool import AudioTool
    from tools.evaluation_system import EvaluationSystem

    # Show evaluation summary if requested
    if args.eval_summary:
        evaluator = EvaluationSystem()
        evaluator.print_evaluation_summary()
        return
    
    # Handle voice processing modes
    if args.split_voice:
        if not args.file_path:
            print("Error: file_path required for --split-voice")
            return
        from tools.voice_processor import VoiceProcessor
        print(f"Splitting voice file: {args.file_path}")
        processor = VoiceProcessor()
        notes = [n.strip() for n in args.notes.split(',')]
        processor.process_voice_file(args.file_path, "voice_samples", notes)
        print("Voice processing complete. Samples saved to 'voice_samples'.")
        return

    if args.clone_voice:
        if not args.file_path:
            print("Error: file_path required for --clone-voice")
            return
        from tools.voice_cloner import VoiceCloner
        print(f"Cloning voice from: {args.file_path}")
        cloner = VoiceCloner()
        cloner.clone_voice(args.file_path)
        return
    
    if not args.file_path:
        print("Error: file_path is required")
        return

    print(f"Processing file: {args.file_path}")
    print(f"User ID: {args.user_id}")

    # Initialize agents
    library = LibraryAgent()
    extractor = ExtractionAgent(
        library_agent=library,
        enable_tools=True
    )
    corrector = CorrectionTool(library_agent=library, user_id=args.user_id)
    evaluator = EvaluationSystem(library_agent=library)
    
    # Check Library
    music_data = library.get_cached_data(args.file_path)

    if not music_data:
        # 1. Extraction with memory
        print("Extracting with memory-enabled agent...")
        music_data = await extractor.extract(args.file_path, user_id=args.user_id)
        
        if not music_data:
            print("Failed to extract music data.")
            return
        
        # Save to library with user context
        library.save_to_library(args.file_path, music_data, user_id=args.user_id)
    else:
        print("Loaded from library.")

    print("Extraction complete.")
    
    # 2. Human-in-the-loop Correction with preference learning
    corrected_data = corrector.review_and_correct(music_data, user_id=args.user_id)
    
    # Learn from corrections
    if corrected_data != music_data:
        extractor.learn_from_correction(music_data, corrected_data, args.user_id)
        library.record_correction_pattern(music_data, corrected_data, args.user_id)
    
    print("Correction complete.")
    
    # 2.5. Human-in-the-loop Evaluation (optional)
    if args.evaluate:
        evaluator.evaluate_extraction(args.file_path, corrected_data, user_id=args.user_id)

    # 3. Audio Generation & Playback
    # Apply user preferences from memory
    preferences = library.get_user_preferences(args.user_id)
    
    # Use preferred tempo if not overridden
    if not args.tempo and preferences.get('default_tempo'):
        args.tempo = str(preferences.get('default_tempo'))
        print(f"Using preferred tempo from memory: {args.tempo}")
    
    # Use preferred hand if not specified
    if args.hand == 'both' and preferences.get('preferred_hand') != 'both':
        args.hand = preferences.get('preferred_hand')
        print(f"Using preferred hand from memory: {args.hand}")
    
    voice_dir = "voice_samples"
    if not os.path.exists(voice_dir):
        voice_dir = None
        
    player = AudioTool(voice_samples_dir=voice_dir)
    
    # Interactive Session
    if args.interactive:
        print("\n--- Interactive Session ---")
        print("Commands: play [n], play [start]-[end], next, prev, tempo [bpm], hand [left/right/both], exit")
        
        current_measure = 1
        total_measures = len(corrected_data.get('measures', []))
        if total_measures == 0:
             # Fallback for legacy notes
             total_measures = 1
             
        current_tempo = args.tempo
        current_hands = ['left', 'right']
        if args.hand == 'left': current_hands = ['left']
        elif args.hand == 'right': current_hands = ['right']

        while True:
            cmd = input(f"(Measure {current_measure}/{total_measures}) > ").strip().lower()
            
            if cmd == 'exit':
                break
            elif cmd.startswith('play'):
                parts = cmd.split()
                if len(parts) > 1:
                    rng = parts[1]
                    if '-' in rng:
                        try:
                            s, e = map(int, rng.split('-'))
                            player.play(corrected_data, hands=current_hands, tempo_override=current_tempo, measure_range=(s, e))
                            current_measure = e
                        except:
                            print("Invalid range.")
                    else:
                        try:
                            m = int(rng)
                            player.play(corrected_data, hands=current_hands, tempo_override=current_tempo, measure_range=(m, m))
                            current_measure = m
                        except:
                            print("Invalid measure number.")
                else:
                    # Play all from current
                    player.play(corrected_data, hands=current_hands, tempo_override=current_tempo, measure_range=(current_measure, total_measures))
            
            elif cmd == 'next':
                if current_measure < total_measures:
                    current_measure += 1
                    player.play(corrected_data, hands=current_hands, tempo_override=current_tempo, measure_range=(current_measure, current_measure))
                else:
                    print("End of piece.")
            
            elif cmd == 'prev':
                if current_measure > 1:
                    current_measure -= 1
                    player.play(corrected_data, hands=current_hands, tempo_override=current_tempo, measure_range=(current_measure, current_measure))
                else:
                    print("Already at start.")
            
            elif cmd.startswith('tempo'):
                try:
                    current_tempo = int(cmd.split()[1])
                    # Save tempo preference
                    library.update_preference('tempo', current_tempo, args.user_id)
                    print(f"Tempo set to {current_tempo} (preference saved)")
                except:
                    print("Invalid tempo.")
            
            elif cmd.startswith('hand'):
                h = cmd.split()[1]
                if h in ['left', 'right', 'both']:
                    if h == 'both': current_hands = ['left', 'right']
                    else: current_hands = [h]
                    # Save hand preference
                    library.update_preference('hand', h, args.user_id)
                    print(f"Hand set to {h} (preference saved)")
                else:
                    print("Invalid hand. Use left, right, or both.")
            else:
                print("Unknown command.")
        
    else:
        # Non-interactive play
        hands_to_play = ['left', 'right']
        if args.hand == 'left':
            hands_to_play = ['left']
        elif args.hand == 'right':
            hands_to_play = ['right']
            
        player.play(corrected_data, hands=hands_to_play, tempo_override=args.tempo)


async def main():
    parser = argparse.ArgumentParser(
        description="Sheet Reader Agent - Music Assistant and Extraction Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive chat mode (Music Assistant)
  python main.py --interactive
  python main.py "find a piece by Bach"
  python main.py --file /path/to/sheet.png

  # Extraction workflow mode (legacy)
  python main.py /path/to/sheet.png --interactive
  python main.py /path/to/sheet.png --evaluate
        """
    )
    
    # Mode selection
    parser.add_argument("--mode", choices=['assistant', 'extract'], default='assistant',
                       help="Mode: 'assistant' for chat mode, 'extract' for extraction workflow (default: assistant)")
    
    # Music Assistant arguments
    parser.add_argument("query", nargs="?", help="Query for the music assistant")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    parser.add_argument("--file", "-f", help="Path to image/PDF file to upload")
    
    # Extraction workflow arguments
    parser.add_argument("file_path", nargs="?", help="Path to music sheet for extraction workflow")
    parser.add_argument("--split-voice", action="store_true", 
                       help="Split voice file into samples (extraction mode)")
    parser.add_argument("--notes", help="Comma-separated notes for voice splitting", 
                       default="C4,D4,E4,F4,G4,A4,B4,C5")
    parser.add_argument("--hand", choices=['left', 'right', 'both'], default='both',
                       help="Which hand to play (extraction mode)")
    parser.add_argument("--tempo", help="Override tempo (BPM) (extraction mode)")
    parser.add_argument("--clone-voice", action="store_true", 
                       help="Clone voice sample (extraction mode)")
    parser.add_argument("--evaluate", action="store_true", 
                       help="Run evaluation after extraction")
    parser.add_argument("--user-id", help="User identifier", default="default_user")
    parser.add_argument("--eval-summary", action="store_true", 
                       help="Show evaluation summary and exit")
    
    args = parser.parse_args()
    
    # Determine mode based on arguments
    if args.file_path or args.split_voice or args.clone_voice or args.eval_summary:
        # Extraction workflow mode
        await run_extraction_workflow(args)
    else:
        # Music Assistant mode (default)
        await run_music_assistant(args)


if __name__ == "__main__":
    asyncio.run(main())
