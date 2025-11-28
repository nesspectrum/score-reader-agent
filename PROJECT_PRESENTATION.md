# Music Assistant Agent - Project Presentation

## Problem Statement

**The Problem:** Musicians and music enthusiasts face significant friction when trying to find, access, and digitize sheet music:

1. **Fragmented Discovery** - Sheet music is scattered across multiple platforms (MuseScore, IMSLP, personal collections)
2. **Analog-to-Digital Gap** - Physical sheet music or handwritten scores require manual transcription, which is time-consuming and error-prone
3. **No Intelligent Search** - Existing tools lack semantic understanding (e.g., "find a sad piano piece in C minor")
4. **Lost Knowledge** - Rare or personal compositions aren't digitized and remain inaccessible

**Why It Matters:** 
- **Accessibility** - Democratizes access to music education and performance
- **Preservation** - Digitizes and preserves musical heritage
- **Efficiency** - Saves musicians hours of manual transcription work
- **Discovery** - Enables intelligent search across 250k+ public domain pieces

---

## Why Agents?

Agents are the **perfect solution** for this problem because:

### 1. **Multi-Step Reasoning Required**
The workflow isn't a simple API call—it requires decision-making:
```
User: "Find Moonlight Sonata"
Agent: Search PDMX → Found? → Yes → Fetch metadata → Offer playback
                    → No → Suggest upload → Convert with HOMR → Save to library
```

### 2. **Tool Orchestration**
The agent needs to coordinate multiple specialized tools:
- **Search tools** (local CSV, Vertex AI Search)
- **Computer vision** (HOMR for OCR)
- **File management** (LibraryAgent for caching)
- **Multimodal input** (text + images)

### 3. **Context Awareness**
The agent maintains conversation state:
- Remembers what the user searched for
- Understands when to suggest alternatives
- Learns from user corrections (future enhancement)

### 4. **Human-in-the-Loop**
The agent can ask for confirmation before:
- Adding new pieces to the library
- Running expensive operations (HOMR conversion)
- Making destructive changes

**Without agents**, you'd need a rigid state machine with hardcoded logic. **With agents**, the LLM handles the complexity naturally.

---

## What You Created

### Overall Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Music Assistant Agent                     │
│                  (Google ADK + Gemini 2.5)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌─────────────┐
│ Search Tools │ │   HOMR   │ │   Library   │
│              │ │  (OCR)   │ │   Agent     │
│ • PDMX CSV   │ │          │ │             │
│ • Vertex AI  │ │ Image→   │ │ • Caching   │
│   Search     │ │ MusicXML │ │ • Metadata  │
└──────────────┘ └──────────┘ └─────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  PDMX Dataset  │
              │  (254k pieces) │
              │                │
              │ • MusicXML     │
              │ • Metadata     │
              │ • PDFs         │
              └────────────────┘
```

### Key Components

1. **MusicAssistantAgent** (`agents/music_assistant.py`)
   - Single unified agent built on Google ADK
   - Multimodal (text + image input)
   - Tool-calling capabilities

2. **Search Layer**
   - **Local Search** (`tools/pdmx_tool.py`) - Fast CSV-based search (254k items)
   - **Cloud Search** (`tools/vertex_search_tool.py`) - Vertex AI Search for semantic queries

3. **Digitization Pipeline**
   - **HOMR Integration** (`tools/homr_tool.py`) - Converts sheet music images to MusicXML
   - **MusicXML Parser** (`tools/musicxml_parser.py`) - Extracts structured data

4. **Library Management**
   - **LibraryAgent** (`agents/library_agent.py`) - Caches converted files, manages metadata
   - **Hash-based deduplication** - Prevents duplicate processing

5. **Data Infrastructure**
   - **PDMX Dataset** - 254,077 public domain pieces from MuseScore
   - **Vertex AI Datastore** - Cloud-based searchable index

---

## Demo

### Example 1: Finding Existing Music

```bash
$ python app.py "Find Moonlight Sonata"

🎵 Music Assistant Initialized
Ask me to find a piece of music, or upload a sheet to digitize.

Assistant > I found several versions of "Moonlight Sonata" in the database:

1. **Piano Sonata No. 14 "Moonlight Sonata"** by Ludwig van Beethoven
   - Rating: 4.92/5 (1,234 ratings)
   - Complexity: Advanced
   - MuseScore: https://musescore.com/...
   
Would you like me to play this or search for a different arrangement?
```

### Example 2: Uploading New Sheet Music

```bash
$ python app.py -f my_handwritten_score.png "Convert this to MusicXML"

🎵 Music Assistant Initialized
📎 Uploading file: my_handwritten_score.png

Assistant > I can see your handwritten score. Let me convert it to MusicXML...

[Calling convert_image_to_musicxml...]
✓ Conversion complete: my_handwritten_score.musicxml

I've extracted:
- Title: "Waltz in A Minor"
- Time Signature: 3/4
- Key: A minor
- 32 measures

Would you like me to add this to your library?
```

### Example 3: Interactive Session

```bash
$ python app.py -i

🎵 Music Assistant Initialized
In interactive mode, type 'upload <filepath>' to upload an image.

User > Find Clair de Lune
Assistant > Found "Clair de Lune" by Claude Debussy...

User > upload rare_piece.png
📎 Uploading file: rare_piece.png
Assistant > Converting your sheet music...

User > exit
```

---

## The Build

### Technologies Used

#### Core Framework
- **Google ADK (Agent Development Kit)** - Agent orchestration, tool calling, session management
- **Gemini 2.5 Flash** - Multimodal LLM (text + vision)
- **Python 3.10** - Primary language

#### Data & Search
- **PDMX Dataset** - 254k public domain MusicXML files from Zenodo
- **Pandas/CSV** - Local search index (225MB CSV)
- **Vertex AI Search** - Cloud-based semantic search (optional)
- **Google Cloud Storage** - Data hosting

#### Computer Vision & Parsing
- **HOMR** - Handwritten Optical Music Recognition (external repo)
- **MusicXML** - Standard music notation format
- **OpenCV** (via HOMR) - Image processing

#### Infrastructure
- **Poetry** - Dependency management
- **dotenv** - Environment configuration
- **subprocess** - HOMR integration

### Development Process

1. **Data Acquisition** (Day 1)
   - Downloaded PDMX dataset (4GB compressed)
   - Explored CSV structure and metadata
   - Built local search tool

2. **Agent Architecture** (Day 2)
   - Started with multi-agent design (ExtractionAgent, LibraryAgent, ValidationAgent)
   - Simplified to single MusicAssistantAgent
   - Integrated ADK Runner and session management

3. **Tool Integration** (Day 3)
   - Connected HOMR for image→MusicXML conversion
   - Built MusicXML parser
   - Added multimodal file upload

4. **Cloud Infrastructure** (Day 4)
   - Set up Vertex AI Search datastore
   - Implemented cloud search tool
   - Imported sample data to GCS

### Key Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **ADK API complexity** | Studied docs, used `inspect` to discover method signatures |
| **HOMR integration** | Wrapped as subprocess tool with timeout handling |
| **Large dataset (4GB)** | CSV-based local search + optional cloud search |
| **Multimodal input** | Used `google.genai.types.Blob` for inline image data |
| **Session management** | Implemented proper ADK Runner with InMemorySessionService |

---

## If I Had More Time, This Is What I'd Do

### 1. **Enhanced Search Capabilities** (1 week)
- [ ] **Semantic search** - "Find a sad piano piece" → search by mood/genre
- [ ] **Audio similarity** - Upload a recording → find matching sheet music
- [ ] **Fuzzy matching** - Handle typos and variations in piece names

### 2. **Improved HOMR Integration** (3 days)
- [ ] **Batch processing** - Convert multiple pages at once
- [ ] **Error correction** - Human-in-the-loop to fix OCR mistakes
- [ ] **Confidence scores** - Show which parts of the conversion are uncertain

### 3. **Playback & Audio** (1 week)
- [ ] **MIDI generation** - Convert MusicXML → MIDI for playback
- [ ] **Audio synthesis** - Generate realistic piano audio
- [ ] **MuseScore integration** - Directly open pieces in MuseScore

### 4. **User Experience** (1 week)
- [ ] **Web UI** - React frontend with drag-drop upload
- [ ] **Real-time streaming** - Show conversion progress
- [ ] **Music notation rendering** - Display sheet music in browser

### 5. **Advanced Features** (2 weeks)
- [ ] **Collaborative library** - Share collections with other users
- [ ] **Version control** - Track edits and corrections over time
- [ ] **Transposition tool** - Change key signatures automatically
- [ ] **Practice mode** - Slow down tempo, loop sections

### 6. **Production Readiness** (1 week)
- [ ] **Authentication** - User accounts and permissions
- [ ] **Rate limiting** - Prevent abuse of HOMR/search
- [ ] **Monitoring** - Track usage, errors, performance
- [ ] **Deployment** - Containerize and deploy to Cloud Run

### 7. **Data Quality** (Ongoing)
- [ ] **Full PDMX import** - Process all 254k pieces (currently sampled)
- [ ] **Metadata enrichment** - Add genre tags, difficulty ratings
- [ ] **Deduplication** - Merge duplicate arrangements

---

## Conclusion

This project demonstrates how **agents** can solve complex, multi-step problems that require:
- **Reasoning** (search → not found → suggest upload)
- **Tool orchestration** (search, OCR, file management)
- **Multimodal understanding** (text + images)
- **Human collaboration** (confirmations, corrections)

The Music Assistant makes sheet music **discoverable, accessible, and digitizable** for musicians worldwide.

---

**Built with ❤️ using Google ADK and Gemini 2.5**
