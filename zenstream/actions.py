import subprocess
import sys
from pathlib import Path

import streamlit as st
from handlers.audioplayer import AudioPlayer
from handlers.docxviewer import DocXViewer
from handlers.excelviewer import ExcelViewer
from handlers.imageviewer import ImageViewer
from handlers.mermaid import MermaidViewer
from handlers.pandasviewer import PandasViewer
from handlers.pdfviewer import PDFViewer
from handlers.textviewer import TextViewer
from handlers.videoplayer import VideoPlayer
from state import State
from utils import get_ext


class Action:
    handlers = {
        "mp3": [AudioPlayer],
        "ogg": [AudioPlayer],
        "wav": [AudioPlayer],
        "csv": [PandasViewer],
        "pdf": [PDFViewer],
        "jpeg": [ImageViewer],
        "jpg": [ImageViewer],
        "png": [ImageViewer],
        "webm": [VideoPlayer],
        "mp4": [VideoPlayer],
        "avi": [VideoPlayer],
        "xls": [ExcelViewer],
        "xlsx": [ExcelViewer],
        "docx": [DocXViewer],
        "mermaid": [MermaidViewer],
    }
    """A dictionary of file type / handler class list pairs. The handler class
    exposing a `show_file(file_name)` method."""

    _ICONS: dict[str, list[str]] = {
        ":material/audio_file:": ["mp3", "ogg", "wav"],
        ":material/csv:": ["csv"],
        ":material/text_snippet:": ["txt", "md"],
        ":material/code:": ["py"],
        ":material/settings:": ["ini", "yaml", "yml", "json", "toml"],
        ":material/run_circle:": ["bat", "sh"],
        ":material/picture_as_pdf:": ["pdf"],
        ":material/image:": ["jpeg", "jpg", "png"],
        ":material/movie:": ["webm", "mp4", "avi"],
        ":material/table:": ["xls", "xlsx"],
        ":material/history_toggle_off:": ["log"],
        ":material/dictionary:": ["docx"],
    }
    """Reverse-lookup mapping: icon → list of extensions."""

    _EXT_ICON: dict[str, str] = {
        ext: icon for icon, exts in _ICONS.items() for ext in exts
    }
    """Flat ext → icon lookup, derived from _ICONS."""

    @staticmethod
    def get_handlers(file_name: str) -> list:
        """Return the handler for the file, defaulting to a text viewer."""
        ext = get_ext(file_name)
        return Action.handlers.get(ext, [TextViewer])

    @staticmethod
    def get_icon(file_name: str) -> str:
        """Return a Streamlit material icon string for the given file."""
        return Action._EXT_ICON.get(get_ext(file_name), ":material/article:")

    @staticmethod
    def delete_file(file_name: str):
        try:
            Path(file_name).unlink(missing_ok=True)
        except Exception as e:
            st.error(f"Error deleting file: {e}")

        State.set("current_file", "")
        State.set("delete_file", "")

    @staticmethod
    def run_file(file_name: str):
        """Run the given file. Currently, only python files are supported."""
        print(f"Running {file_name}")
        match get_ext(file_name):
            case "py":
                PythonFile.run(file_name)
            case _:
                return []


class PythonFile:
    @staticmethod
    def run(file_name: str):
        subprocess.run(
            [sys.executable, file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
            # env=os.environ.copy(),
            encoding="utf-8",
        )
