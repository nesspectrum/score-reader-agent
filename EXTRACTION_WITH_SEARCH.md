# Piece Name Extraction and Sample Music Search

## Overview

The `ExtractionAgent` has been enhanced to:
1. **Extract piece name and composer** from music sheets
2. **Automatically search for sample music** files after extraction
3. **Use Google Search tool** to find audio samples, MIDI files, and sheet music

## Changes Made

### 1. Enhanced Extraction Schema

The extraction now includes two new fields:
- `piece_name`: The title/name of the piece (e.g., "Prelude in C Major")
- `composer`: The composer's name if visible (e.g., "Bach", "Beethoven")

### 2. New Search Tool

Added `search_sample_music()` function in `tools/agent_tools.py`:
- Takes piece name and optional composer
- Builds a search query for sample music
- Uses Google Search tool if available
- Returns search results with links to music resources

### 3. Automatic Search After Extraction

After extracting music data, the agent:
1. Extracts piece name and composer
2. Automatically searches for sample music
3. Adds search results to the extracted data under `sample_music_search`
4. Displays search results to the user

## Usage

### Basic Extraction with Search

```python
from agents.extraction_agent import ExtractionAgent
from agents.library_agent import LibraryAgent
from agents.memory_service import SimpleMemoryService

# Initialize
memory_service = SimpleMemoryService()
library = LibraryAgent(memory_service=memory_service)
extractor = ExtractionAgent(
    memory_service=memory_service,
    library_agent=library,
    enable_tools=True  # Enables search functionality
)

# Extract (automatically searches for samples)
music_data = await extractor.extract("sheet.pdf", user_id="user123")

# Access search results
if 'sample_music_search' in music_data:
    search = music_data['sample_music_search']
    print(f"Found {len(search.get('results', []))} results")
    print(f"Search URL: {search.get('search_url')}")
```

### Extracted Data Structure

```json
{
  "piece_name": "Prelude in C Major",
  "composer": "Bach",
  "key": "C Major",
  "tempo": "120",
  "measures": [...],
  "sample_music_search": {
    "status": "success",
    "piece_name": "Prelude in C Major",
    "composer": "Bach",
    "query": "Prelude in C Major Bach piano sheet music audio sample midi",
    "search_url": "https://www.google.com/search?q=...",
    "results": [...],
    "suggested_sites": [
      "https://imslp.org",
      "https://musescore.com",
      ...
    ]
  }
}
```

## Search Tool Details

### Function: `search_sample_music(piece_name, composer=None)`

**Parameters:**
- `piece_name` (str): Name of the music piece
- `composer` (str, optional): Composer name

**Returns:**
- Dictionary with search results and links

**Search Query Format:**
```
"{piece_name} {composer} piano sheet music audio sample midi"
```

### Google Search Integration

The agent includes the `google_search` tool from ADK:
- Automatically added if available
- Can be used by the agent during extraction
- Provides web search capabilities

### Fallback Behavior

If Google Search tool is not available:
- Returns search query for manual use
- Provides direct Google search URL
- Lists suggested music sites (IMSLP, MuseScore, etc.)

## Example Output

```
Extracting notes from sheet.pdf...
✓ Extraction validated successfully

🔍 Searching for sample music: Prelude in C Major
   Composer: Bach
   ✓ Found 3 results:
      1. Bach - Prelude in C Major (BWV 846) - IMSLP
         https://imslp.org/wiki/...
      2. Prelude in C Major - MuseScore
         https://musescore.com/...
      3. Free Piano Sheet Music - Prelude in C Major
         https://www.free-scores.com/...
```

## Integration with Tools

The search functionality integrates with:
- **Validation tools**: Validates extracted piece name
- **Memory service**: Stores search queries for future reference
- **Library agent**: Can cache search results

## Future Enhancements

Potential improvements:
1. Download sample audio files automatically
2. Compare extracted notes with sample MIDI files
3. Use search results to improve extraction accuracy
4. Cache search results in library
5. Support multiple music databases (IMSLP API, MuseScore API)

## Testing

Test with a music sheet:

```bash
python3 main.py "resources/Bach_Prelude in C major, BWV 846.pdf" --user-id "test_user"
```

Expected output includes:
- Piece name extraction
- Composer identification
- Automatic sample music search
- Search results with links

