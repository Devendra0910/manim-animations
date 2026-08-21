# Manim Animations

Mathematical animations built with [Manim Community Edition](https://www.manim.community/).

## Setup

Requires Python 3.11 (Manim's deps don't yet support the very latest Python), ffmpeg, and cairo/pango.

```bash
# macOS via Homebrew
brew install ffmpeg cairo pango pkg-config

# create venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install manim
```

LaTeX (for `MathTex`) is optional and not required by the scenes in this repo — they use plain
`Text()` so you can skip installing a LaTeX distribution. To add LaTeX support later:

```bash
brew install --cask basictex
```

## Scenes

### `collatz.py` — `CollatzScene`

Animates the Collatz conjecture (3n+1 problem): the rule, a step-by-step worked example
(n=27 by default), and a plotted graph of the full trajectory.

```bash
source .venv/bin/activate
manim -pql collatz.py CollatzScene   # fast preview (480p15)
manim -pqh collatz.py CollatzScene   # high quality (1080p60)
```
