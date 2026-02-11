"""
Example: Using tools and sub-agents in the score-reader-agent system
Demonstrates:
1. FunctionTools for validation and statistics
2. Sub-agents for specialized tasks
3. Multi-agent workflows
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agents.extraction_agent import ExtractionAgent
from agents.library_agent import LibraryAgent
from agents.validation_agent import ValidationAgent
from agents.memory_service import SimpleMemoryService
from tools.agent_tools import validate_music_data, get_music_statistics


async def example_function_tools():
    """Example: Using function tools directly"""
    print("=" * 80)
    print("EXAMPLE 1: Using Function Tools Directly")
    print("=" * 80)
    
    # Sample music data
    sample_data = {
        "key": "C Major",
        "tempo": "120",
        "measures": [
            {
                "id": 1,
                "right_hand": [
                    {"notes": ["C4", "E4"], "duration": "quarter"},
                    {"notes": ["G4"], "duration": "quarter"}
                ],
                "left_hand": [
                    {"notes": ["C3"], "duration": "half"}
                ]
            }
        ]
    }
    
    # Use validation tool
    print("\n1. Validating music data...")
    validation = validate_music_data(sample_data)
    print(f"   Valid: {validation.get('valid')}")
    print(f"   Errors: {validation.get('errors', [])}")
    print(f"   Warnings: {validation.get('warnings', [])}")
    
    # Use statistics tool
    print("\n2. Getting music statistics...")
    stats = get_music_statistics(sample_data)
    if stats.get('status') == 'success':
        s = stats.get('statistics', {})
        print(f"   Key: {s.get('key')}")
        print(f"   Measures: {s.get('measure_count')}")
        print(f"   Unique Pitches: {s.get('unique_pitches', [])}")


async def example_agent_with_tools():
    """Example: Agent using tools automatically"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Agent with Tools")
    print("=" * 80)
    
    memory_service = SimpleMemoryService()
    library = LibraryAgent(memory_service=memory_service)
    
    # Create extraction agent with tools enabled
    extractor = ExtractionAgent(
        memory_service=memory_service,
        library_agent=library,
        enable_tools=True
    )
    
    print("\nExtractionAgent created with tools:")
    print(f"  - validate_music_data")
    print(f"  - get_music_statistics")
    print(f"  - get_note_frequency")
    print(f"  - suggest_corrections")
    print(f"  - get_user_preferences")
    
    print("\nThe agent can now use these tools during extraction to:")
    print("  - Validate extracted data")
    print("  - Calculate statistics")
    print("  - Get note frequencies")
    print("  - Suggest corrections")
    print("  - Access user preferences")


async def example_sub_agent():
    """Example: Using ValidationAgent as a sub-agent"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Sub-Agent for Validation")
    print("=" * 80)
    
    memory_service = SimpleMemoryService()
    library = LibraryAgent(memory_service=memory_service)
    
    # Create validation agent
    validator = ValidationAgent(library_agent=library)
    
    # Sample data to validate
    sample_data = {
        "key": "C Major",
        "tempo": "120",
        "measures": [
            {
                "id": 1,
                "right_hand": [
                    {"notes": ["C4", "E4"], "duration": "quarter"}
                ],
                "left_hand": [
                    {"notes": ["C3"], "duration": "half"}
                ]
            }
        ]
    }
    
    print("\nValidating music data with ValidationAgent...")
    result = await validator.validate(sample_data, user_id="test_user")
    
    print(f"\nValidation Results:")
    print(f"  Valid: {result.get('is_valid')}")
    print(f"  Statistics: {result.get('statistics', {}).get('measure_count')} measures")
    print(f"  Suggestions: {len(result.get('suggestions', {}))} suggestions")


async def example_multi_agent_workflow():
    """Example: Multi-agent workflow with extraction and validation"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Multi-Agent Workflow")
    print("=" * 80)
    
    memory_service = SimpleMemoryService()
    library = LibraryAgent(memory_service=memory_service)
    
    # Create extraction agent
    extractor = ExtractionAgent(
        memory_service=memory_service,
        library_agent=library,
        enable_tools=True
    )
    
    # Create validation agent
    validator = ValidationAgent(library_agent=library)
    
    print("\nMulti-agent workflow:")
    print("  1. ExtractionAgent extracts music data from sheet")
    print("  2. ExtractionAgent uses tools to validate internally")
    print("  3. ValidationAgent performs additional validation")
    print("  4. Both agents can access shared memory and preferences")
    
    # Note: In a real scenario, you would:
    # 1. Extract with extractor.extract(file_path)
    # 2. Validate with validator.validate(extracted_data)
    # 3. Use results to improve extraction


async def main():
    """Run all examples"""
    await example_function_tools()
    await example_agent_with_tools()
    await example_sub_agent()
    await example_multi_agent_workflow()
    
    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  - FunctionTools provide reusable functions to agents")
    print("  - Sub-agents specialize in specific tasks")
    print("  - Agents can use tools automatically during generation")
    print("  - Multiple agents can share memory and preferences")


if __name__ == "__main__":
    asyncio.run(main())

