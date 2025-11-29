# 🎵 Score Reader Agent

An intelligent AI-powered music assistant that converts music sheet images to MusicXML format, searches extensive music databases, and manages your digital music library using Google's Agent Development Kit (ADK).

## ✨ Features

- **📸 Image to MusicXML Conversion**: Convert music sheet images (PNG, JPG, PDF) to MusicXML format using HOMR (Handwritten Optical Music Recognition)
- **🔍 Intelligent Music Search**: Search through local PDMX database (250K+ pieces) and Google Cloud Vertex AI Search datastore
- **📚 Library Management**: Organize and manage your digital music sheet library with metadata extraction
- **🤖 Multi-Agent Architecture**: Specialized agents for different tasks (Music Assistant, Library Agent, Extraction Agent)
- **💾 Persistent Memory**: Long-term memory service for learning user preferences and patterns
- **🎯 Interactive CLI**: User-friendly command-line interface for easy interaction

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud Project with Vertex AI enabled
- Google API Key or Application Default Credentials

### Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:nesspectrum/score_reader_agent.git
   cd score_reader_agent
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env  # Create .env file
   # Edit .env with your credentials
   ```
   
   Required environment variables:
   ```env
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_CLOUD_MODEL=gemini-2.5-flash-lite
   GOOGLE_API_KEY=your-api-key
   PDMX_DATASTORE_ID=pdmx-musicxml
   ```

5. **Set up Google Cloud authentication:**
   ```bash
   gcloud auth application-default login
   ```

## 📖 Usage

### Interactive Mode

Start the interactive assistant:

```bash
python main.py --interactive
```

Example interaction:
```
User > find a piece by Bach
Assistant > I found "Prelude in C Major" by Bach. Would you like to know more?

User > upload /path/to/sheet.png
Assistant > Converting image to MusicXML...
```

### Single Query Mode

```bash
python main.py "find Chopin Prelude"
```

### File Upload

```bash
python main.py --file /path/to/music-sheet.png
```

## 🏗️ Project Structure

```
score_reader_agent/
├── agents/              # AI agents
│   ├── music_assistant.py    # Main music assistant agent
│   ├── library_agent.py      # Library management agent
│   ├── extraction_agent.py   # Music extraction agent
│   └── validation_agent.py   # Data validation agent
├── tools/               # Tool functions
│   ├── homr_tool.py          # HOMR image conversion
│   ├── pdmx_tool.py          # PDMX database search
│   ├── vertex_search_tool.py # Vertex AI Search
│   └── library_manager.py   # Library file operations
├── utils/               # Utility scripts
│   ├── check_api_key.py      # API key validation
│   ├── create_pdmx_library.py # PDMX library import
│   ├── setup_pdmx_datastore.py # Datastore setup
│   └── ...                    # Other utility scripts
├── tests/               # Test files
│   ├── test_*.py             # Unit and integration tests
│   └── test_*.json           # Test data files
├── main.py              # Main application entry point
├── playground.py        # Interactive playground
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🔧 Configuration

### Google Cloud Setup

1. **Enable required APIs:**
   ```bash
   gcloud services enable discoveryengine.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   ```

2. **Set up Vertex AI Search Datastore:**
   - See [PDMX_DATASTORE_SETUP.md](./PDMX_DATASTORE_SETUP.md) for detailed instructions
   - Or use the setup script:
     ```bash
     python setup_pdmx_datastore.py --project-id YOUR_PROJECT_ID
     ```

### PDMX Database

Import PDMX data into your local library:

```bash
python create_pdmx_library.py --sample-size 1000
```

## 🎯 Key Capabilities

### Music Sheet Conversion
- Supports PNG, JPG, JPEG formats
- Uses HOMR (Handwritten Optical Music Recognition) for accurate conversion
- Outputs standard MusicXML format

### Search Capabilities
- **Local Search**: Fast search through imported PDMX database
- **Cloud Search**: Semantic search via Vertex AI Search datastore
- **Smart Suggestions**: Automatically suggests file upload when search fails

### Library Management
- Automatic metadata extraction (composer, key, tempo, measures)
- User preference learning
- Caching and deduplication

## 📚 Documentation

For detailed project documentation including problem statement, architecture, and development details, see [PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md).

## 📝 License

This project is part of the Nesspectrum Solutions organization.

## 🙏 Acknowledgments

This project builds upon excellent open-source work:

- **[HOMR](https://github.com/liebharc/homr)** - Optical Music Recognition (OMR) software that transforms camera pictures of sheet music into machine-readable MusicXML format. HOMR employs segmentation techniques and transformer models to identify musical symbols and convert them to MusicXML.

- **[PDMX](https://github.com/pnlong/PDMX/)** - Public Domain MusicXML dataset containing 250K+ public domain music scores. This project uses PDMX data for music search and library management.

- **Google ADK** - Agent Development Kit for building AI agents
- **Vertex AI** - Google Cloud AI platform

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with ❤️ by Nesspectrum Solutions**
