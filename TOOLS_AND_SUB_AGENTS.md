# Tools and Sub-Agents Documentation

## Overview

The sheet-reader-agent now supports using tools as **FunctionTools** and **Sub-Agents** following ADK patterns. This enables:
- Agents to call functions during extraction
- Specialized sub-agents for validation and analysis
- Reusable tool functions across multiple agents

## FunctionTools

FunctionTools are Python functions wrapped as tools that agents can call automatically.

### Available Tools

Located in `tools/agent_tools.py`:

1. **`get_note_frequency(pitch: str)`**
   - Returns frequency in Hz for a musical note
   - Example: `get_note_frequency("C4")` → `261.63 Hz`

2. **`generate_tone(frequency_hz: float, duration_sec: float)`**
   - Generates audio tone data
   - Returns sample count and metadata

3. **`validate_music_data(music_data: Dict)`**
   - Validates extracted music data structure
   - Checks for required fields, correct types, etc.
   - Returns validation errors and warnings

4. **`get_music_statistics(music_data: Dict)`**
   - Calculates statistics about music data
   - Returns measure count, event counts, unique pitches, etc.

5. **`suggest_corrections(music_data: Dict, user_preferences: Dict)`**
   - Suggests corrections based on patterns and preferences
   - Non-interactive version for agent use

6. **`get_user_preferences(user_id: str, library_agent)`**
   - Retrieves user preferences from library agent
   - Returns tempo, hand preferences, etc.

### Using FunctionTools in Agents

```python
from google.adk.tools import FunctionTool
from tools.agent_tools import validate_music_data, get_music_statistics

# Create agent with tools
agent = ExtractionAgent(
    enable_tools=True,  # Enable tools
    library_agent=library_agent
)

# Tools are automatically available to the agent during generation
# The agent can call them as needed
```

### Direct Tool Usage

```python
from tools.agent_tools import validate_music_data, get_music_statistics

# Use tools directly
music_data = {...}
validation = validate_music_data(music_data)
stats = get_music_statistics(music_data)
```

## Sub-Agents

Sub-agents are specialized agents that can be used within other agents or as standalone validators.

### ValidationAgent

A specialized agent for validating and improving music data:

```python
from agents.validation_agent import ValidationAgent

# Create validation agent
validator = ValidationAgent(library_agent=library_agent)

# Validate music data
result = await validator.validate(music_data, user_id="user123")

# Result contains:
# - validation: validation results
# - statistics: music statistics
# - suggestions: improvement suggestions
# - is_valid: boolean validation status
```

### Using Sub-Agents in Workflows

```python
# Multi-agent workflow
extractor = ExtractionAgent(enable_tools=True, library_agent=library)
validator = ValidationAgent(library_agent=library)

# 1. Extract
extracted_data = await extractor.extract(file_path, user_id)

# 2. Validate with sub-agent
validation_result = await validator.validate(extracted_data, user_id)

# 3. Use results
if not validation_result['is_valid']:
    # Handle validation errors
    pass
```

## Integration in ExtractionAgent

The `ExtractionAgent` now includes tools by default:

```python
extractor = ExtractionAgent(
    memory_service=memory_service,
    library_agent=library_agent,
    enable_tools=True  # Default: True
)
```

**Tools available to ExtractionAgent:**
- `validate_music_data` - Validates extracted data
- `get_music_statistics` - Calculates statistics
- `get_note_frequency` - Gets note frequencies
- `suggest_corrections` - Suggests improvements
- `get_user_preferences` - Accesses user preferences

The agent automatically:
1. Validates extracted data after extraction
2. Checks for suggestions based on user preferences
3. Uses tools during generation when needed

## Examples

See `examples/multi_agent_example.py` for complete examples:

1. **Direct Tool Usage** - Using tools as functions
2. **Agent with Tools** - Agent using tools automatically
3. **Sub-Agent Validation** - Using ValidationAgent
4. **Multi-Agent Workflow** - Combining multiple agents

Run examples:
```bash
python examples/multi_agent_example.py
```

## Architecture

```
ExtractionAgent (with tools)
├── FunctionTool: validate_music_data
├── FunctionTool: get_music_statistics
├── FunctionTool: get_note_frequency
├── FunctionTool: suggest_corrections
└── FunctionTool: get_user_preferences

ValidationAgent (sub-agent)
├── FunctionTool: validate_music_data
├── FunctionTool: get_music_statistics
└── FunctionTool: suggest_corrections

LibraryAgent (shared)
└── Provides preferences to both agents
```

## Benefits

1. **Automatic Validation**: Agents validate their own output
2. **Reusability**: Tools can be shared across agents
3. **Specialization**: Sub-agents focus on specific tasks
4. **Flexibility**: Mix function tools and sub-agents as needed
5. **ADK Compatibility**: Follows ADK patterns for tools and agents

## Future Enhancements

- More specialized sub-agents (e.g., AudioGenerationAgent)
- AgentTool wrappers for complex workflows
- Tool chaining and composition
- Dynamic tool loading based on context

