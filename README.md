# Genaki Tobira Anki Deck Generator

This tool generates Anki decks for Japanese vocabulary from the Tobira textbook, using vocabulary and definitions from the [jisho](https://github.com/di5codan/jisho) submodule. Audio is automatically generated for each vocabulary term.

## Features

- **Three card types:**  
  1. Vocab → Meaning + Kana + Audio  
  2. Audio → Meaning + Vocab + Kana  
  3. Meaning → Vocab + Kana + Audio
- **Automatic audio generation** using [translate-shell](https://github.com/soimort/translate-shell)
- **Decks and audio files** are output to the `build/` directory

## Setup

1. **Clone the repo and submodule:**
   ```bash
   git clone https://github.com/yourusername/genaki-tobira.git
   cd genaki-tobira
   git submodule update --init --recursive
   ```

2. **Install dependencies:**
   ```bash
   sudo apt install translate-shell
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

Generate a deck for a specific Tobira chapter (1–15):

```bash
python generate_deck.py <chapter_number>
```

Example:

```bash
python generate_deck.py 1
```

- The deck will be saved as `build/Tobira_Lesson_<chapter_number>.apkg`
- Audio files are saved in `build/audio/`

## Directory Structure

```
genaki-tobira/
├── generate_deck.py
├── build/
│   ├── Tobira_Lesson_<chapter_number>.apkg
│   └── audio/
│       ├── <vocab>.mp3
│       └── .gitignore
├── jisho/ (submodule)
│   └── Tobira/
│       └── 第<chapter_number>課.md
│   └── Vocabulary/
│       └── <vocab>.md
```

## Notes

- The script will automatically create the `build/` and `build/audio/` directories if they do not exist.
- The `build/audio/.gitignore` file is created to prevent audio files from being tracked by git.
- Make sure you have internet access for audio generation.

