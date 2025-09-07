import os
import re
import sys
import subprocess
import genanki

JISHO_PATH = './jisho'
TOBIRA_PATH = os.path.join(JISHO_PATH, 'Tobira')
QUARTET_PATH = os.path.join(JISHO_PATH, 'Quartet')
VOCAB_PATH = os.path.join(JISHO_PATH, 'Vocabulary')
BUILD_PATH = './build'
AUDIO_PATH = os.path.join(BUILD_PATH, 'audio')

VOCAB_MEANING_FRONT = '<center><h1>{{Vocab}}</h1></center>'
VOCAB_MEANING_BACK = '<center>{{FrontSide}}<hr id="answer"><h2>{{Meaning}}<br>{{Kana}}<br>{{Audio}}</h2></center>'

AUDIO_MEANING_FRONT = '<center>{{Audio}}</center>'
AUDIO_MEANING_BACK = '<center>{{FrontSide}}<hr id="answer"><h2>{{Meaning}}<br>{{Vocab}}<br>{{Kana}}</h2></center>'

MEANING_VOCAB_FRONT = '<center><h1>{{Meaning}}</h1></center>'
MEANING_VOCAB_BACK = '<center>{{FrontSide}}<hr id="answer"><h2>{{Vocab}}<br>{{Kana}}<br>{{Audio}}</h2></center>'

def ensure_dirs():
    os.makedirs(AUDIO_PATH, exist_ok=True)
    os.makedirs(BUILD_PATH, exist_ok=True)
    gitignore_path = os.path.join(AUDIO_PATH, '.gitignore')
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write('*\n')

def parse_vocab_list(chapter_md):
    with open(chapter_md, encoding='utf-8') as f:
        lines = f.readlines()
    vocab = []
    for line in lines:
        m = re.match(r'\[(.+?)\]\(../Vocabulary/.+?\.md\)', line.strip())
        if m:
            vocab.append(m.group(1))
    return vocab

def parse_vocab_info(vocab_md, vocab):
    with open(vocab_md, encoding='utf-8') as f:
        lines = f.readlines()
    meaning = ''
    kana = ''
    for i, line in enumerate(lines):
        if line.startswith('# '):
            meaning = line[2:].strip()
            # Try to get kana from next line, otherwise fallback to vocab
            if i+1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and not next_line.startswith('#'):
                    kana = next_line
                else:
                    kana = vocab
            else:
                kana = vocab
            break
    return meaning, kana

def get_audio_filename(vocab):
    return f'{vocab}.mp3'

def generate_audio(vocab, kana):
    audio_path = os.path.join(AUDIO_PATH, get_audio_filename(vocab))
    if not os.path.exists(audio_path):
        print(f'Generating audio for {vocab}...')
        try:
            subprocess.run(
                ['trans', '-t', 'ja', '-download-audio-as', get_audio_filename(vocab), kana],
                cwd=AUDIO_PATH,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except Exception as e:
            print(f'Audio generation failed for {vocab}: {e}')

def get_deck_id(textbook, chapter):
    prefix = 20594001
    chapter_num = int(chapter)
    # Use different base IDs for different textbooks
    if textbook.lower() == 'quartet':
        prefix = 20594002
    deck_id = int(f"{prefix:08d}{chapter_num:02d}")
    return deck_id

def get_model(model_id, name, fields, qfmt, afmt):
    return genanki.Model(
        model_id,
        name,
        fields=[{'name': field} for field in fields],
        templates=[{'name': name, 'qfmt': qfmt, 'afmt': afmt}]
    )

def main():
    if len(sys.argv) != 3:
        print('Usage: python generate_deck.py <textbook> <chapter_number>')
        print('Examples:')
        print('  python generate_deck.py tobira 1')
        print('  python generate_deck.py quartet 1')
        sys.exit(1)
    
    ensure_dirs()
    textbook = sys.argv[1].lower()
    chapter = sys.argv[2]
    
    # Determine the correct path based on textbook
    if textbook == 'tobira':
        textbook_path = TOBIRA_PATH
        textbook_display = 'Tobira'
    elif textbook == 'quartet':
        textbook_path = QUARTET_PATH
        textbook_display = 'Quartet'
    else:
        print(f'Unknown textbook: {textbook}. Use "tobira" or "quartet".')
        sys.exit(1)
    
    chapter_md = os.path.join(textbook_path, f'第{chapter}課.md')
    if not os.path.exists(chapter_md):
        print(f'Chapter file not found: {chapter_md}')
        sys.exit(1)
    vocab_list = parse_vocab_list(chapter_md)
    media_files = []
    vocab_infos = []

    # Prepare models
    vocab_meaning_model = get_model(
        1607392300, f'{textbook_display} Vocab->Meaning',
        ['Vocab', 'Meaning', 'Kana', 'Audio'],
        VOCAB_MEANING_FRONT, VOCAB_MEANING_BACK
    )
    audio_meaning_model = get_model(
        1607392301, f'{textbook_display} Audio->Meaning',
        ['Audio', 'Meaning', 'Vocab', 'Kana'],
        AUDIO_MEANING_FRONT, AUDIO_MEANING_BACK
    )
    meaning_vocab_model = get_model(
        1607392302, f'{textbook_display} Meaning->Vocab',
        ['Meaning', 'Vocab', 'Kana', 'Audio'],
        MEANING_VOCAB_FRONT, MEANING_VOCAB_BACK
    )

    # Gather vocab info and generate audio
    for vocab in vocab_list:
        vocab_md = os.path.join(VOCAB_PATH, f'{vocab}.md')
        if not os.path.exists(vocab_md):
            print(f'Vocab file not found: {vocab_md}')
            continue
        meaning, kana = parse_vocab_info(vocab_md, vocab)
        audio_file = get_audio_filename(vocab)
        generate_audio(vocab, kana)
        audio_tag = f'[sound:{audio_file}]'
        audio_path = os.path.join(AUDIO_PATH, audio_file)
        if os.path.exists(audio_path):
            media_files.append(audio_path)
        vocab_infos.append((vocab, meaning, kana, audio_tag))

    notes = []
    # Card type 1: Vocab->Meaning
    for vocab, meaning, kana, audio_tag in vocab_infos:
        notes.append(genanki.Note(
            model=vocab_meaning_model,
            fields=[vocab, meaning, kana, audio_tag]
        ))
    # Card type 2: Audio->Meaning
    for vocab, meaning, kana, audio_tag in vocab_infos:
        notes.append(genanki.Note(
            model=audio_meaning_model,
            fields=[audio_tag, meaning, vocab, kana]
        ))
    # Card type 3: Meaning->Vocab
    for vocab, meaning, kana, audio_tag in vocab_infos:
        notes.append(genanki.Note(
            model=meaning_vocab_model,
            fields=[meaning, vocab, kana, audio_tag]
        ))

    deck_id = get_deck_id(textbook, chapter)
    deck = genanki.Deck(
        deck_id,
        f'{textbook_display} Lesson {chapter}'
    )
    for note in notes:
        deck.add_note(note)
    output_path = os.path.join(BUILD_PATH, f'{textbook_display}_Lesson_{chapter}.apkg')
    genanki.Package(deck, media_files=media_files).write_to_file(output_path)
    print(f'Deck written to {output_path}')

if __name__ == '__main__':
    main()