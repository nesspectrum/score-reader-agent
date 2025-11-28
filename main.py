import os
import argparse
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents.extraction_agent import ExtractionAgent
from tools.library_manager import LibraryManager as LibraryAgent
from tools.correction_tool import CorrectionTool
from tools.audio_tool import AudioTool
from tools.evaluation_system import EvaluationSystem

async def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Music Sheet Reader with Memory & Evaluation")
    parser.add_argument("file_path", nargs="?", help="Path to the music sheet (image or PDF) OR audio file for splitting")
    parser.add_argument("--split-voice", action="store_true", help="If set, treats file_path as a voice recording to split into samples")
    parser.add_argument("--notes", help="Comma-separated list of notes for splitting (e.g. 'C4,D4,E4')", default="C4,D4,E4,F4,G4,A4,B4,C5")
    parser.add_argument("--hand", choices=['left', 'right', 'both'], default='both', help="Which hand to play (default: both)")
    parser.add_argument("--tempo", help="Override tempo (BPM)", default=None)
    parser.add_argument("--clone-voice", action="store_true", help="If set, treats file_path as a voice sample to clone (pitch shift)")
    parser.add_argument("--interactive", action="store_true", help="Enter interactive mode after extraction")
    parser.add_argument("--evaluate", action="store_true", help="Run human-in-the-loop evaluation after extraction")
    parser.add_argument("--user-id", help="User identifier for memory and preference tracking", default="default_user")
    parser.add_argument("--eval-summary", action="store_true", help="Show evaluation summary and exit")
    args = parser.parse_args()
    
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

    if args.split_voice:
        from tools.voice_processor import VoiceProcessor
        print(f"Splitting voice file: {args.file_path}")
        processor = VoiceProcessor()
        notes = [n.strip() for n in args.notes.split(',')]
        processor.process_voice_file(args.file_path, "voice_samples", notes)
        print("Voice processing complete. Samples saved to 'voice_samples'.")
        return

    if args.clone_voice:
        from tools.voice_cloner import VoiceCloner
        print(f"Cloning voice from: {args.file_path}")
        cloner = VoiceCloner()
        cloner.clone_voice(args.file_path)
        return

    print(f"Processing file: {args.file_path}")

    # 0. Check Library
    library = LibraryAgent()
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

if __name__ == "__main__":
    asyncio.run(main())
