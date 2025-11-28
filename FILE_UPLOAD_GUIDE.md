# Music Assistant - File Upload Guide

## Upload Methods

### 1. Command Line (Non-Interactive)
Upload a file with an optional query:
```bash
python app.py --file path/to/sheet.png "Convert this to MusicXML"
```

Or just upload without a query:
```bash
python app.py -f path/to/sheet.pdf
```

### 2. Interactive Mode
Start interactive mode:
```bash
python app.py -i
```

Then upload files during the conversation:
```
User > upload path/to/sheet.png
```

The agent will receive the image and can use its tools (like HOMR) to convert it.

## Supported File Types
- PNG images (`.png`)
- JPEG images (`.jpg`, `.jpeg`)
- PDF files (`.pdf`)

## Example Workflow

1. **Search for existing piece:**
   ```bash
   python app.py "Find Moonlight Sonata"
   ```

2. **Upload new sheet if not found:**
   ```bash
   python app.py -f my_sheet.png "Convert this sheet to MusicXML"
   ```

3. **Interactive session:**
   ```bash
   python app.py -i
   User > Find Clair de Lune
   User > upload /path/to/new_piece.pdf
   User > exit
   ```
