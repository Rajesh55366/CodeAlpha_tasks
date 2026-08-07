# AI Music Generation with LSTM

Generates new piano music by training an LSTM (Long Short-Term Memory) network
on a corpus of MIDI files, then sampling new note sequences and rendering
them back to a playable `.mid` file.

Pipeline: **collect MIDI data → preprocess with music21 → train LSTM → generate → save as MIDI**

## Project structure

```
music_gen/
├── requirements.txt
├── data/
│   ├── raw_midi/        # .mid files go here (downloaded or your own)
│   └── processed/        # preprocessed note-sequence data (auto-generated)
├── models/                # saved model checkpoints (auto-generated)
├── output/                # generated .mid files land here
└── src/
    ├── download_data.py   # fetches a small public-domain MIDI dataset
    ├── preprocess.py      # MIDI -> note/chord sequences using music21
    ├── model.py            # LSTM architecture (Keras/TensorFlow)
    ├── train.py             # trains the model on preprocessed data
    └── generate.py         # samples new sequences and writes a .mid file
```

## 1. Setup

```bash
cd music_gen
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`music21` also needs a MIDI player registered if you want to auto-play audio
(optional — not required to just generate the .mid file).

## 2. Get MIDI data

Two options, both handled by `download_data.py`:

- **Classical piano set** (default, small, good for a first run): clones a
  public GitHub repo of classical piano MIDI files into `data/raw_midi/`.
- **MAESTRO v3.0.0** (bigger, higher quality, ~120 hours of piano performances):
  pass `--dataset maestro` to download and unzip a subset from Magenta's
  public MAESTRO bucket.

```bash
python src/download_data.py --dataset classical      # quick start (~200 files)
# or
python src/download_data.py --dataset maestro --limit 50   # 50 MAESTRO pieces
```

You can also just drop your own `.mid`/`.midi` files into `data/raw_midi/`.

## 3. Preprocess

Parses every MIDI file into a flat sequence of notes/chords with `music21`,
builds a vocabulary, and saves fixed-length input/output training sequences.

```bash
python src/preprocess.py
```

Outputs `data/processed/sequences.npz` and `data/processed/vocab.pkl`.

## 4. Train

```bash
python src/train.py --epochs 100 --batch-size 64
```

Checkpoints (`.keras` files) are saved to `models/` after every epoch that
improves loss, plus a final `models/final_model.keras`.

## 5. Generate music

```bash
python src/generate.py --model models/final_model.keras --length 500 --output output/generated.mid
```

This samples a new note sequence from the trained model and converts it back
into a MIDI file you can play in any media player, DAW, or `music21`'s
built-in player.

## Notes on the approach

- **Representation**: each MIDI file is flattened into a sequence of tokens,
  where a token is either a single pitch (`"64"`) or a chord written as
  dot-joined pitches (`"60.64.67"`), plus the note's duration. This is the
  standard `music21`-based encoding used in most LSTM music-generation
  tutorials (e.g. Skuldur's Classical-Piano-Composer).
- **Model**: a stacked LSTM with dropout, trained to predict the next token
  given the previous `SEQUENCE_LENGTH` tokens (categorical cross-entropy,
  Adam optimizer). This is intentionally the "simple, well-documented"
  architecture rather than a GAN — easier to train and debug from scratch.
- **Sampling**: generation uses temperature-based sampling from the softmax
  output so the output isn't purely greedy (which tends to loop).

## Extending this

- Swap `model.py`'s architecture for a GAN (e.g. a MidiNet/MuseGAN-style
  generator + discriminator) if you want to explore that route later —
  `preprocess.py`'s output format stays the same.
- Add instrument-aware / multi-track handling (currently flattens to a single
  melodic/chordal line, which is standard for a first project).
- Condition generation on a musical style/genre by training separate models
  per genre folder.
