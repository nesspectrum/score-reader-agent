# Memory and Evaluation System Documentation

## Overview

The sheet-reader-agent has been enhanced with:
1. **Memory-enabled agents** that learn from past extractions and user corrections
2. **User preference tracking** that remembers tempo, hand preferences, and correction patterns
3. **Human-in-the-loop evaluation system** for continuous improvement

## Key Changes

### 1. ExtractionAgent (`agents/extraction_agent.py`)
- **Memory Integration**: Loads past extraction patterns and user preferences before extraction
- **Learning from Corrections**: Stores correction patterns when users fix extraction errors
- **Context-Aware Extraction**: Uses memory to improve accuracy on similar music sheets

**New Methods:**
- `_load_extraction_memory()`: Retrieves relevant extraction patterns from memory
- `_get_user_preferences_context()`: Gets user preferences to guide extraction
- `learn_from_correction()`: Stores correction patterns for future learning

### 2. LibraryAgent (`agents/library_agent.py`)
- **Preference Management**: Stores and retrieves user preferences (tempo, hand, etc.)
- **Correction Pattern Tracking**: Records common corrections to learn user preferences
- **Memory Integration**: Stores library entries and preferences in memory service

**New Methods:**
- `get_user_preferences()`: Retrieves user preferences from disk and memory
- `update_preference()`: Updates and stores user preferences
- `record_correction_pattern()`: Records corrections for learning

### 3. CorrectionTool (`tools/correction_tool.py`)
- **Quick Edit Mode**: Fast correction for common fields (key, tempo)
- **Preference Suggestions**: Suggests default values based on user preferences
- **Automatic Learning**: Records corrections automatically for future improvements

**New Features:**
- Quick edit mode (`q`) for common corrections
- Preference-aware suggestions
- Automatic correction pattern recording

### 4. EvaluationSystem (`tools/evaluation_system.py`)
- **Human-in-the-Loop Evaluation**: Collects user feedback on extraction quality
- **Preference Collection**: Gathers user preferences during evaluation
- **Performance Tracking**: Maintains evaluation history and statistics

**Key Features:**
- Accuracy ratings for key, tempo, and notes extraction
- Correction collection and analysis
- Evaluation summaries and statistics
- Integration with memory service for learning

### 5. SimpleMemoryService (`agents/memory_service.py`)
- **Memory Storage**: Persistent memory storage with disk backup
- **Search Functionality**: Semantic search across memories
- **Type-Based Retrieval**: Get memories by type (preferences, corrections, etc.)

## Usage

### Basic Usage with Memory

```bash
# Extract with memory (learns from past extractions)
python main.py sheet.pdf --user-id "user123"

# Extract and evaluate
python main.py sheet.pdf --evaluate --user-id "user123"

# View evaluation summary
python main.py --eval-summary
```

### Interactive Mode with Preferences

```bash
# Interactive mode saves preferences automatically
python main.py sheet.pdf --interactive --user-id "user123"

# Commands in interactive mode:
# - tempo 120          # Sets tempo and saves preference
# - hand left          # Sets hand preference and saves it
# - play 1-4           # Plays measures 1-4
```

### Evaluation Workflow

1. **Extract and Evaluate:**
   ```bash
   python main.py sheet.pdf --evaluate --user-id "user123"
   ```

2. **Provide Feedback:**
   - Rate accuracy (1-5) for key, tempo, and notes
   - Provide corrections if needed
   - Share preferences (default tempo, preferred hand)

3. **View Summary:**
   ```bash
   python main.py --eval-summary
   ```

## Memory Storage

### Memory Types

1. **Extraction Patterns**: Stored when extraction completes
   - Metadata: key, tempo, measure count, file hash

2. **Correction Patterns**: Stored when user corrects extraction
   - Metadata: original vs corrected values

3. **User Preferences**: Stored when user sets preferences
   - Types: tempo, hand preference, extraction style

4. **Evaluation Results**: Stored during evaluation
   - Metadata: ratings, corrections, feedback

### Storage Locations

- **Memory**: `memory/memories.json`
- **User Preferences**: `library/user_preferences.json`
- **Evaluations**: `evaluations/evaluations.json`
- **Library Cache**: `library/{file_hash}.json`

## Benefits

1. **Improved Accuracy**: Agents learn from past mistakes and user corrections
2. **Personalization**: System adapts to user preferences over time
3. **Continuous Improvement**: Evaluation system tracks performance and identifies patterns
4. **User Experience**: Preferences are remembered and applied automatically

## Example Workflow

```bash
# First extraction - no memory
python main.py sheet1.pdf --user-id "alice" --evaluate

# User provides feedback and corrections
# System learns preferences and patterns

# Second extraction - uses memory
python main.py sheet2.pdf --user-id "alice"
# System automatically applies learned preferences
# Extraction is more accurate based on past corrections

# View progress
python main.py --eval-summary
```

## Integration with ADK Sample Patterns

The implementation follows patterns from `resources/adk_agent_sample.py`:
- Memory service setup similar to `setup_memory_service()`
- Memory-enabled agents similar to `create_memory_enabled_agent()`
- Evaluation dataset creation similar to `create_evaluation_dataset()`
- Human-in-the-loop patterns similar to `create_simulation_scenario()`

## Future Enhancements

- Integration with Google ADK's native memory service (when available)
- Database-backed memory for production use
- Advanced search with embeddings
- Multi-user preference management
- Automated evaluation metrics

