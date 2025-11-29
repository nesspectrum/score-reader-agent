# Score Reader Agent - Project Documentation 🎵

Let's face it— Finding public music in XML format is difficult. 
🎹 Here's what we're up against:

- **Fragmented search**: Want to find a piece suitable for your practice level? Better know the exact title, composer, and have access to 5 different tools. Good luck! 🔍

- **Manual digitization**: Converting physical sheet music or images to MusicXML to benefit from tools such as [MuseScore](https://musescore.com/)? Time-consuming and error-prone! 😫

- **Limited accessibility**: So many beautiful pieces trapped as images or PDFs, unable to be searched or analyzed. It's like having a library where you can't use the card catalog! 📚

- **No unified interface**: Juggling conversion tools, search engines, library managers, and playback systems. It's exhausting! 🤹

But here's the thing—this problem matters because it's the bridge between old-school music notation and modern computational tools. We're making music faster to learn, easier to organize, and more accessible to everyone. Plus, who doesn't want to digitize their grandma's sheet music collection? 🎼

---

Why agents? Because they're basically the perfect solution! Here's why:

1. **Complex Multi-Step Workflows**: image analysis → conversion → metadata extraction → search → library management. Agents are the perfect conductors for this orchestra! 🎻

2. **Natural Language Interaction**: Users don't think in APIs. They think: *"Find me something by Bach"* or *"Turn this photo into MusicXML"*. Agents get it. They speak human! 🗣️

3. **Adaptive Problem-Solving**: Search failed? No problem! The agent says "Hey, why don't you upload that file instead?" It's like having a helpful friend who always has a backup plan. 🤝

4. **Specialized Sub-Agents**: Think of it like a band—each agent has their own instrument:
   - **MusicAssistantAgent**: The frontman, handling queries and conversions
   - **LibraryAgent**: The librarian, managing search and organization
   - **ExtractionAgent**: The perfectionist, extracting and validating data
   - **ValidationAgent**: The quality control inspector, making sure everything's perfect

5. **Memory and Learning**: Agents remember your preferences (like preferring 120 BPM or left-hand-only practice). They learn from mistakes. They're basically getting smarter every day! 🧠✨

6. **Tool Integration**: Agents are like Swiss Army knives—they know which tool to use when. HOMR for conversion? Check. Vertex AI for search? Check. PDMX database? Check. They've got it all! 🛠️

---

### Architecture

Behold! A multi-agent system that's basically a well-oiled music-processing machine:

```
🎤 User Interface (CLI/Interactive Chat)
    ↓
🎯 MusicAssistantAgent (The Boss)
    ├── 📚 LibraryAgent (The Librarian)
    └── 🔬 ExtractionAgent (The Scientist)
    ↓
🛠️ Tools Layer (The Toolbox)
    ├── 🖼️ HOMR Tool (Image → MusicXML wizard)
    ├── 🔍 PDMX Tool (Local search master)
    ├── ☁️ Vertex Search Tool (Cloud search guru)
    ├── 📁 Library Manager (File whisperer)
    └── ✅ Validation Tools (Quality police)
    ↓
🌐 External Services (The Powerhouses)
    ├── HOMR (Optical Music Recognition)
    ├── PDMX Database (250K+ pieces!)
    ├── Vertex AI Search (Semantic search magic)
    └── Google Cloud Platform (The cloud)
```

### Key Components

**Agents (The Team):**
- **MusicAssistantAgent**: The conversationalist who handles queries, converts images, and keeps everything running smoothly
- **LibraryAgent**: The search expert who knows where everything is (local and cloud!)
- **ExtractionAgent**: The data extraction wizard with validation superpowers
- **ValidationAgent**: The perfectionist ensuring everything meets quality standards

**Tools (The Arsenal):**
- **HOMR Tool**: Turns images/PDFs into MusicXML like magic ✨
- **PDMX Tool**: Searches through 250K+ pieces with fuzzy matching (it's smart!)
- **Vertex Search Tool**: Semantic search that understands what you *mean*, not just what you *say*
- **Library Manager**: Handles files, caching, metadata, and remembers your preferences
- **Correction Tool**: Learns from your corrections (it's getting smarter!)

**Services (The Infrastructure):**
- **Session Service**: Keeps track of conversations (InMemorySessionService)
- **Memory Service**: Remembers everything (InMemoryMemoryService) - it's like an elephant!
- **Library Service**: File-based library with JSON metadata (organized and efficient)

### Data Flow (The Journey)

1. **User Query** → MusicAssistantAgent receives your natural language request
2. **Intent Recognition** → Agent figures out what you want (search? convert? manage?)
3. **Tool Selection** → Agent picks the right tool or calls in a specialist sub-agent
4. **Execution** → Tools do their thing (search, convert, file operations)
5. **Response Generation** → Agent formats everything nicely and responds
6. **Memory Update** → Your preferences get saved for next time (it remembers!)

---

## Demo

### Interactive Chat Mode

```bash
python main.py --interactive
```

**Real Example (because examples are fun!):**
```
🎵 Music Assistant Initialized
Ask me to find a piece of music or upload a sheet to digitize.

User > find a piece by Bach

Assistant > 🎹 Found several pieces by Bach:
  1. Prelude in C Major, BWV 846 - Key: C Major
  2. Minuet in G Major, BWV 114 - Key: G Major
  Want more details?

User > find a piece by Nesspectrum

Assistant >I couldn't find any pieces by Bach that are not preludes in the local library. Would you like me to search the cloud datastore or perhaps try a different composer?

User > cloud store

Assistant > Searching datastore: pdxm in global
Query: Nesspectrum
Found 0 results
I couldn't find any pieces by Bach that are not preludes in the cloud datastore either.
Would you like to upload a piece by nesspectrum?

User > Yes, upload /home/user/sheet.png

📎 Uploading file: /home/user/sheet.png
Assistant > Converting image to MusicXML...
✨ Successfully converted! Output: /home/user/sheet.musicxml
  Key: D Major | Time: 4/4 | Measures: 32 | Tempo: 120 BPM

Assistant > I still need more information to upload the file. I require the metadata, which should include the 'data' key with extraction results. Please provide the composer, title, and any other relevant details.

User > the title is experimental piece and the composer is Nessepctrum and it is written for piano.

Assistant > Saved to library: library/be41635a1aa045f80f491e96b499660f338826cf07830d2dae4e6a08b329fb81.json
I have successfully added the music sheet with the title "experimental piece" by composer "Nesspectrum" to the library.


```

### What Makes It Cool

- **Intelligent Search**: Searches both local PDMX database AND Vertex AI cloud (double the power!)
- **Automatic Fallback**: Search failed? No worries, it suggests uploading instead (helpful!)
- **Image Conversion**: Turns PNG/JPG/PDF into MusicXML using HOMR (like magic!)
- **Library Management**: Automatically extracts metadata and organizes everything (neat!)
- **Context Awareness**: Remembers your preferences and past interactions (it's learning!)

---

### The Stack

**Core (The Foundation):**
- Google Agent Development Kit (ADK)
- Google Gemini 2.5 Flash Lite 
- Python 3.10+ 

**Cloud Services (The Power):**
- Vertex AI Search - semantic search that's actually smart
- Google Cloud AI Platform - where the magic happens

**Music Processing (The Specialists):**
- PDMX Dataset - 250K+ pieces of public domain goodness
- HOMR - Optical Music Recognition (A transformer based image to xml conversion!)
- MusicXML - the universal language of digital music


### Development Process (How We Built It)

1. **Architecture Design**: Designed a hierarchical agent structure (like building a team!)
2. **Agent Implementation**: Built the root orchestrator and specialized sub-agents
3. **Tool Development**: Wrapped external systems as Python tools (making them play nice!)
4. **Integration**: Connected everything with ADK Runner, Session services, and memory
5. **User Experience**: Built an interactive CLI with streaming responses (smooth!)

### Design Decisions (Why We Did It This Way)

1. **Multi-Agent Architecture**: Separated concerns = easier to maintain and optimize (divide and conquer!)
2. **Tool-Based Design**: External capabilities as tools = modular and testable (clean code!)
3. **Memory Integration**: ADK memory service = personalization that actually works
5. **Human-in-the-Loop** (Future): Learns from user feedback (getting smarter every day!)

### Challenges Overcome (The Victories)

- **HOMR Integration**: Wrapped a complex CLI tool with proper error handling (took some work!)
- **Memory Management**: Managed session and user memory using ADK's built-in tools.
- **Agent Coordination**: Managed complex interactions using ADK's sub-agent pattern (teamwork!)


## If I Had More Time (The Wishlist)

1. **Human-in-the-Loop & Critic Validation**: Interactive validation workflows where users can review and correct extraction results, plus AI critic agents that validate quality and provide confidence scores before user review (quality control with AI backup!)

2. **Web Interface**: A beautiful React/Next.js UI with drag-and-drop upload, real-time search, and visual music sheet preview (so satisfying!)

3. **Enhanced OMR & Learning System**: Fine-tuned models for better accuracy, handwritten recognition support, and a learning system that improves from user corrections over time (getting smarter!)

4. **Mobile App & Cloud Infrastructure**: Native iOS/Android app with camera integration, plus scalable cloud backend with distributed processing for handling large workloads (scale to the moon!)
