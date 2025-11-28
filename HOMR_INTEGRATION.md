# HOMR (Handwritten Optical Music Recognition) Integration

## What is HOMR?

HOMR is a tool that converts images of sheet music into MusicXML format using computer vision and machine learning. It's located in the `homr/` directory of this project.

## How HOMR is Used in the Music Assistant

### 1. **As an Agent Tool**

The `convert_image_to_musicxml` function from `tools/homr_tool.py` is registered as a tool that the MusicAssistantAgent can call:

```python
# In agents/music_assistant.py
tools = [
    FunctionTool(func=convert_image_to_musicxml),  # HOMR integration
    # ... other tools
]
```

### 2. **Workflow**

When a user uploads a music sheet image:

1. **User uploads image** (via `--file` flag or `upload` command)
2. **Agent receives the image** as part of the multimodal message
3. **Agent decides to use HOMR** based on its instructions
4. **Agent calls `convert_image_to_musicxml(image_path)`**
5. **HOMR processes the image:**
   - Runs via `poetry run homr <image_path>` (or direct Python execution)
   - Outputs a `.musicxml` file in the same directory
6. **Tool returns the XML path** to the agent
7. **Agent can then:**
   - Parse the MusicXML to extract structured data
   - Save it to the library
   - Offer playback options

### 3. **Technical Details**

The `homr_tool.py` implementation:

```python
def convert_image_to_musicxml(image_path: str, output_dir: Optional[str] = None):
    # 1. Locate HOMR installation
    homr_dir = os.path.join(project_root, "homr")
    
    # 2. Try to run via poetry
    homr_command = ["poetry", "run", "homr"]
    
    # 3. Execute HOMR
    result = subprocess.run(
        homr_command + [image_path],
        cwd=homr_dir,
        timeout=300  # 5 minute timeout
    )
    
    # 4. Return path to generated .musicxml file
    return {"status": "success", "xml_path": expected_xml}
```

## Current Status

⚠️ **HOMR needs installation:**
```bash
cd homr
poetry install
```

The tool will automatically detect and use HOMR once it's installed.

## Example Usage

```bash
# Upload an image for conversion
python app.py -f sheet_music.png "Convert this to MusicXML"
```

The agent will:
1. See the image
2. Call `convert_image_to_musicxml("sheet_music.png")`
3. HOMR generates `sheet_music.musicxml`
4. Agent can parse and save it to the library
