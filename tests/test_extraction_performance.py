#!/usr/bin/env python3
"""
Standalone script to test ExtractionAgent performance and improve it with few-shot examples.
Tests extraction accuracy and allows adding examples to improve performance.
"""

import os
import json
import asyncio
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

from agents.extraction_agent import ExtractionAgent
from tools.library_manager import LibraryManager as LibraryAgent
from tools.agent_tools import validate_music_data, get_music_statistics


# ============================================================================
# Few-Shot Examples Database (Image + JSON pairs)
# ============================================================================

FEW_SHOT_EXAMPLES_DIR = "few_shot_examples"
FEW_SHOT_EXAMPLES = []  # Will be loaded from files


def load_few_shot_examples_from_directory(directory: str = FEW_SHOT_EXAMPLES_DIR) -> List[Dict[str, Any]]:
    """
    Load few-shot examples from directory structure:
    few_shot_examples/
        example1.png
        example1.json
        example2.png
        example2.json
        ...
    
    Returns:
        List of example dictionaries with image_path and json_data
    """
    examples = []
    
    if not os.path.exists(directory):
        print(f"⚠️  Few-shot examples directory not found: {directory}")
        print(f"   Creating directory structure...")
        os.makedirs(directory, exist_ok=True)
        return examples
    
    # Find all image files
    image_extensions = ['.png', '.jpg', '.jpeg', '.pdf']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend([
            f for f in os.listdir(directory)
            if f.lower().endswith(ext) and not f.startswith('.')
        ])
    
    # Match images with their JSON files
    for image_file in image_files:
        base_name = os.path.splitext(image_file)[0]
        json_file = os.path.join(directory, f"{base_name}.json")
        
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)
                
                examples.append({
                    "image_path": os.path.join(directory, image_file),
                    "json_path": json_file,
                    "description": json_data.get('description', base_name),
                    "json_data": json_data
                })
                print(f"✅ Loaded example: {base_name}")
            except Exception as e:
                print(f"⚠️  Error loading {json_file}: {e}")
        else:
            print(f"⚠️  JSON file not found for {image_file}: {json_file}")
    
    return examples


def format_few_shot_examples_with_images(examples: List[Dict[str, Any]]) -> str:
    """
    Format few-shot examples as a string for the prompt.
    Includes references to example images and their JSON outputs.
    """
    if not examples:
        return ""
    
    formatted = "\n\nFew-shot examples for reference:\n"
    formatted += "Below are example music sheets and their correct JSON extractions:\n\n"
    
    for i, ex in enumerate(examples, 1):
        formatted += f"Example {i}: {ex.get('description', f'Example {i}')}\n"
        formatted += f"Image: {os.path.basename(ex['image_path'])}\n"
        formatted += "Correct JSON extraction:\n"
        formatted += json.dumps(ex['json_data'], indent=2)
        formatted += "\n\n"
    
    formatted += "Use these examples as reference for the correct format and structure.\n"
    return formatted


# ============================================================================
# Performance Testing Functions
# ============================================================================

def format_few_shot_examples(examples: List[Dict[str, Any]]) -> str:
    """Format few-shot examples as a string for the prompt (legacy support)."""
    formatted = "\n\nFew-shot examples for reference:\n"
    for i, ex in enumerate(examples, 1):
        formatted += f"\nExample {i}: {ex.get('description', f'Example {i}')}\n"
        example_data = ex.get('json_data') or ex.get('example', {})
        formatted += json.dumps(example_data, indent=2)
        formatted += "\n"
    return formatted


def calculate_accuracy_metrics(extracted: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate accuracy metrics comparing extracted vs expected data."""
    metrics = {
        "key_match": extracted.get('key') == expected.get('key'),
        "tempo_match": extracted.get('tempo') == expected.get('tempo'),
        "piece_name_match": extracted.get('piece_name') == expected.get('piece_name'),
        "composer_match": extracted.get('composer') == expected.get('composer'),
        "measure_count_match": len(extracted.get('measures', [])) == len(expected.get('measures', [])),
        "total_score": 0,
        "max_score": 5
    }
    
    # Calculate total measures
    extracted_measures = extracted.get('measures', [])
    expected_measures = expected.get('measures', [])
    
    # Compare measures
    measure_accuracy = []
    min_measures = min(len(extracted_measures), len(expected_measures))
    
    for i in range(min_measures):
        ext_measure = extracted_measures[i]
        exp_measure = expected_measures[i]
        
        # Compare right hand events
        ext_rh = ext_measure.get('right_hand', [])
        exp_rh = exp_measure.get('right_hand', [])
        rh_match = len(ext_rh) == len(exp_rh)
        
        # Compare left hand events
        ext_lh = ext_measure.get('left_hand', [])
        exp_lh = exp_measure.get('left_hand', [])
        lh_match = len(ext_lh) == len(exp_lh)
        
        measure_accuracy.append({
            "measure_id": i + 1,
            "right_hand_match": rh_match,
            "left_hand_match": lh_match,
            "events_match": rh_match and lh_match
        })
    
    metrics["measure_accuracy"] = measure_accuracy
    metrics["measures_compared"] = min_measures
    
    # Calculate total score
    score = sum([
        metrics["key_match"],
        metrics["tempo_match"],
        metrics["piece_name_match"],
        metrics["composer_match"],
        metrics["measure_count_match"]
    ])
    metrics["total_score"] = score
    
    return metrics


def print_performance_report(metrics: Dict[str, Any], extraction_time: float):
    """Print a formatted performance report."""
    print("\n" + "=" * 80)
    print("PERFORMANCE REPORT")
    print("=" * 80)
    
    print(f"\n⏱️  Extraction Time: {extraction_time:.2f} seconds")
    print(f"\n📊 Accuracy Metrics:")
    print(f"   Key Match:        {'✅' if metrics['key_match'] else '❌'}")
    print(f"   Tempo Match:      {'✅' if metrics['tempo_match'] else '❌'}")
    print(f"   Piece Name Match: {'✅' if metrics['piece_name_match'] else '❌'}")
    print(f"   Composer Match:   {'✅' if metrics['composer_match'] else '❌'}")
    print(f"   Measure Count:    {'✅' if metrics['measure_count_match'] else '❌'}")
    
    print(f"\n📈 Overall Score: {metrics['total_score']}/{metrics['max_score']}")
    
    if metrics.get('measure_accuracy'):
        print(f"\n🎵 Measure-by-Measure Accuracy:")
        for m in metrics['measure_accuracy']:
            rh = "✅" if m['right_hand_match'] else "❌"
            lh = "✅" if m['left_hand_match'] else "❌"
            print(f"   Measure {m['measure_id']}: RH {rh} | LH {lh}")
    
    print("=" * 80)


# ============================================================================
# Enhanced Extraction Agent with Few-Shot Examples
# ============================================================================

class EnhancedExtractionAgent(ExtractionAgent):
    """ExtractionAgent enhanced with few-shot examples (image + JSON pairs)."""
    
    def __init__(self, *args, few_shot_examples: Optional[List[Dict[str, Any]]] = None, 
                 few_shot_dir: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load examples from directory if provided
        if few_shot_dir:
            self.few_shot_examples = load_few_shot_examples_from_directory(few_shot_dir)
        elif few_shot_examples:
            self.few_shot_examples = few_shot_examples
        else:
            # Try to load from default directory
            self.few_shot_examples = load_few_shot_examples_from_directory()
    
    async def extract(self, file_path, user_id: Optional[str] = None, use_few_shot: bool = True):
        """Extract with few-shot examples."""
        print(f"Extracting notes from {file_path}...")
        
        # Load the file
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            return None

        # Determine mime type
        mime_type = "image/jpeg"
        if file_path.lower().endswith(".png"):
            mime_type = "image/png"
        elif file_path.lower().endswith(".pdf"):
            mime_type = "application/pdf"
        
        # Load memory context
        memory_context = self._load_extraction_memory()
        preferences_context = self._get_user_preferences_context()
        
        # Add few-shot examples
        few_shot_context = ""
        example_images = []
        
        if use_few_shot and self.few_shot_examples:
            # Format examples with JSON data
            few_shot_context = format_few_shot_examples_with_images(self.few_shot_examples)
            # Collect example images to include in the prompt
            example_images = [ex['image_path'] for ex in self.few_shot_examples if 'image_path' in ex]
        
        # Create the prompt with few-shot examples
        prompt = f"""
        Analyze this music sheet (piano/grand staff). Extract the information in JSON format:
        1. "piece_name": The name/title of the piece (e.g., "Prelude in C Major", "Moonlight Sonata"). Extract from the sheet if visible.
        2. "composer": The composer's name if visible on the sheet (e.g., "Bach", "Beethoven", "Chopin").
        3. "key": Key signature (e.g., "C Major").
        4. "tempo": Tempo indication (e.g., "120"), or null.
        5. "measures": A list of measures. Each measure has:
            - "id": Measure number.
            - "right_hand": List of events. Each event has:
                - "notes": List of pitches (e.g., ["C4", "E4"]). Use ["Rest"] for rests.
                - "duration": Duration (e.g., "quarter", "half").
            - "left_hand": List of events (same structure as right_hand).
        
        {few_shot_context}
        {memory_context}
        {preferences_context}
        
        Follow the examples above for correct format. Return ONLY the JSON.
        """
        
        # Generate content using the model directly
        try:
            from google import generativeai as genai
            import os
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            
            model_name = self.model if hasattr(self, 'model') else "gemini-2.5-flash-lite"
            model = genai.GenerativeModel(model_name=model_name)
            
            # Build content parts: prompt + example images + target image
            content_parts = [prompt]
            
            # Add example images first (for few-shot learning)
            for example_img_path in example_images[:3]:  # Limit to 3 examples to avoid token limits
                try:
                    if example_img_path.lower().endswith('.pdf'):
                        example_file = genai.upload_file(
                            path=example_img_path,
                            mime_type="application/pdf"
                        )
                        content_parts.append(example_file)
                    else:
                        # For images, read and encode
                        import base64
                        with open(example_img_path, 'rb') as f:
                            img_data = f.read()
                        img_mime = "image/png" if example_img_path.lower().endswith('.png') else "image/jpeg"
                        content_parts.append({
                            "mime_type": img_mime,
                            "data": base64.b64encode(img_data).decode('utf-8')
                        })
                except Exception as e:
                    print(f"⚠️  Warning: Could not load example image {example_img_path}: {e}")
            
            # Add target image/PDF
            if mime_type == "application/pdf":
                uploaded_file = genai.upload_file(
                    path=file_path,
                    mime_type=mime_type
                )
                content_parts.append(uploaded_file)
            else:
                import base64
                content_parts.append({
                    "mime_type": mime_type,
                    "data": base64.b64encode(file_content).decode('utf-8')
                })
            
            response = model.generate_content(
                content_parts,
                generation_config={"response_mime_type": "application/json"}
            )
            
            json_text = response.text
            if json_text.startswith("```json"):
                json_text = json_text[7:-3]
            elif json_text.startswith("```"):
                json_text = json_text[3:-3]
            
            extracted_data = json.loads(json_text)
            
            # Continue with validation (from parent class logic)
            piece_name = extracted_data.get('piece_name', '')
            composer = extracted_data.get('composer', '')
            
            if self.enable_tools:
                validation_result = validate_music_data(extracted_data)
                if not validation_result.get('valid'):
                    print(f"Warning: Validation found issues: {validation_result.get('errors', [])}")
                else:
                    print("✓ Extraction validated successfully")
            
            # Store extraction pattern
            if self.memory_service and user_id:
                self._store_extraction_pattern(file_path, extracted_data, user_id)
            
            return extracted_data
            
        except Exception as e:
            print(f"Error during extraction: {e}")
            return None
            
        except Exception as e:
            print(f"Error during extraction: {e}")
            return None


# ============================================================================
# Test Functions
# ============================================================================

async def test_extraction_with_file(file_path: str, expected_data: Optional[Dict[str, Any]] = None, 
                                     use_few_shot: bool = True, few_shot_dir: Optional[str] = None):
    """Test extraction with a file and compare with expected data."""
    print(f"\n{'='*80}")
    print(f"TESTING EXTRACTION: {file_path}")
    print(f"{'='*80}")
    
    library = LibraryAgent()
    
    # Create enhanced agent
    agent = EnhancedExtractionAgent(
        library_agent=library,
        enable_tools=True,
        few_shot_dir=few_shot_dir if use_few_shot else None,
        few_shot_examples=None if use_few_shot else []
    )
    
    if use_few_shot and agent.few_shot_examples:
        print(f"📚 Loaded {len(agent.few_shot_examples)} few-shot examples")
    
    start_time = time.time()
    extracted = await agent.extract(file_path, user_id="test_user", use_few_shot=use_few_shot)
    extraction_time = time.time() - start_time
    
    if not extracted:
        print("❌ Extraction failed!")
        return None
    
    print(f"\n✅ Extraction completed in {extraction_time:.2f} seconds")
    print(f"\n📋 Extracted Data:")
    print(f"   Piece Name: {extracted.get('piece_name', 'N/A')}")
    print(f"   Composer: {extracted.get('composer', 'N/A')}")
    print(f"   Key: {extracted.get('key', 'N/A')}")
    print(f"   Tempo: {extracted.get('tempo', 'N/A')}")
    print(f"   Measures: {len(extracted.get('measures', []))}")
    
    # Calculate metrics if expected data provided
    if expected_data:
        metrics = calculate_accuracy_metrics(extracted, expected_data)
        print_performance_report(metrics, extraction_time)
    
    # Show statistics
    stats = get_music_statistics(extracted)
    if stats.get('status') == 'success':
        s = stats.get('statistics', {})
        print(f"\n📊 Statistics:")
        print(f"   Unique Pitches: {s.get('unique_pitch_count', 0)}")
        print(f"   Total Events: {s.get('total_events', 0)}")
        print(f"   Right Hand Events: {s.get('right_hand_events', 0)}")
        print(f"   Left Hand Events: {s.get('left_hand_events', 0)}")
    
    return extracted


async def test_with_examples():
    """Test extraction with few-shot examples vs without."""
    test_file = "resources/Bach_Prelude in C major, BWV 846.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print("\n" + "="*80)
    print("COMPARISON TEST: With vs Without Few-Shot Examples")
    print("="*80)
    
    # Test without few-shot
    print("\n📝 Test 1: WITHOUT Few-Shot Examples")
    result_without = await test_extraction_with_file(test_file, use_few_shot=False)
    
    # Test with few-shot
    print("\n📝 Test 2: WITH Few-Shot Examples")
    result_with = await test_extraction_with_file(test_file, use_few_shot=True)
    
    # Compare
    if result_without and result_with:
        print("\n" + "="*80)
        print("COMPARISON RESULTS")
        print("="*80)
        print(f"Without Few-Shot - Measures: {len(result_without.get('measures', []))}")
        print(f"With Few-Shot    - Measures: {len(result_with.get('measures', []))}")
        print(f"Improvement: {len(result_with.get('measures', [])) - len(result_without.get('measures', []))} measures")


def add_custom_example(image_path: str, json_path: str, description: Optional[str] = None):
    """
    Add a custom few-shot example from image and JSON files.
    
    Args:
        image_path: Path to example image file
        json_path: Path to corresponding JSON extraction file
        description: Optional description (will be read from JSON if not provided)
    """
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return
    
    try:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        desc = description or json_data.get('description', os.path.basename(image_path))
        
        # Copy to examples directory
        examples_dir = FEW_SHOT_EXAMPLES_DIR
        os.makedirs(examples_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        dest_image = os.path.join(examples_dir, f"{base_name}{os.path.splitext(image_path)[1]}")
        dest_json = os.path.join(examples_dir, f"{base_name}.json")
        
        import shutil
        shutil.copy2(image_path, dest_image)
        
        # Ensure JSON has description
        json_data['description'] = desc
        with open(dest_json, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"✅ Added example: {desc}")
        print(f"   Image: {dest_image}")
        print(f"   JSON: {dest_json}")
    except Exception as e:
        print(f"❌ Error adding example: {e}")


def save_examples_to_file(filename: str = "few_shot_examples_index.json"):
    """Save few-shot examples index to a file."""
    examples_dir = FEW_SHOT_EXAMPLES_DIR
    examples = load_few_shot_examples_from_directory(examples_dir)
    
    index = []
    for ex in examples:
        index.append({
            "image": os.path.basename(ex['image_path']),
            "json": os.path.basename(ex['json_path']),
            "description": ex.get('description', '')
        })
    
    with open(filename, 'w') as f:
        json.dump({"examples": index, "directory": examples_dir}, f, indent=2)
    print(f"✅ Saved index of {len(index)} examples to {filename}")


def load_examples_from_file(filename: str = "few_shot_examples.json"):
    """Load few-shot examples from a file."""
    global FEW_SHOT_EXAMPLES
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            FEW_SHOT_EXAMPLES = json.load(f)
        print(f"✅ Loaded {len(FEW_SHOT_EXAMPLES)} examples from {filename}")
    else:
        print(f"⚠️  File not found: {filename}")


# ============================================================================
# Main Test Runner
# ============================================================================

async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ExtractionAgent Performance")
    parser.add_argument("file", nargs="?", help="Path to music sheet file to test")
    parser.add_argument("--expected", help="Path to expected JSON file for comparison")
    parser.add_argument("--few-shot", action="store_true", default=True, help="Use few-shot examples (default: True)")
    parser.add_argument("--no-few-shot", action="store_true", help="Disable few-shot examples")
    parser.add_argument("--add-example", nargs=2, metavar=('IMAGE', 'JSON'), 
                       help="Add a custom example: --add-example image.png extraction.json")
    parser.add_argument("--save-examples", help="Save examples index to file")
    parser.add_argument("--few-shot-dir", default=FEW_SHOT_EXAMPLES_DIR,
                       help=f"Directory containing few-shot examples (default: {FEW_SHOT_EXAMPLES_DIR})")
    parser.add_argument("--compare", action="store_true", help="Compare with vs without few-shot")
    
    args = parser.parse_args()
    
    # Handle example management
    if args.add_example:
        image_path, json_path = args.add_example
        add_custom_example(image_path, json_path)
    
    if args.save_examples:
        save_examples_to_file(args.save_examples)
    
    # Run tests
    if args.compare:
        await test_with_examples()
    elif args.file:
        expected_data = None
        if args.expected:
            with open(args.expected, 'r') as f:
                expected_data = json.load(f)
        
        use_few_shot = args.few_shot and not args.no_few_shot
        await test_extraction_with_file(args.file, expected_data, use_few_shot=use_few_shot, 
                                        few_shot_dir=args.few_shot_dir)
    else:
        print("Usage: python test_extraction_performance.py <file> [options]")
        print("\nOptions:")
        print("  --expected <file>     Compare with expected JSON")
        print("  --few-shot           Use few-shot examples (default)")
        print("  --no-few-shot        Disable few-shot examples")
        print("  --compare            Compare with vs without few-shot")
        print("  --add-example IMAGE JSON  Add custom example (image + JSON pair)")
        print("  --save-examples            Save examples index to file")
        print("  --few-shot-dir DIR        Directory with few-shot examples")


if __name__ == "__main__":
    asyncio.run(main())

