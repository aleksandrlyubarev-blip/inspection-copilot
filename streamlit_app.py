"""Inspection Copilot Streamlit entrypoint."""

from pathlib import Path

from inspection_copilot.ui import render

render(Path(__file__).resolve().parent)
