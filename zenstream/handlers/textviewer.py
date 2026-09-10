from os.path import sep
from pathlib import Path

import pandas as pd
import streamlit as st

from styler import Styler
from utils import get_ext


class TextViewer:
    @staticmethod
    def show_file(file_name: str):
        st.header("Text Viewer")
        st.subheader(file_name.split(sep)[-1])

        if Path(file_name).stat().st_size / (1024**2) > 1.0:  # 1mb
            st.warning("This file is too big to open as text...")
            return

        try:
            with open(file_name, encoding="utf-8") as f:
                lines = f.read()
        except Exception as e:
            st.warning(f"Unable to read as a text file...({e})")
            return

        match get_ext(file_name):
            case "md":
                st.code(
                    lines,
                    line_numbers=True,
                )
                with st.expander("Rendered markdown"):
                    st.markdown(lines)
            case "json":
                st.json(lines)
                try:
                    df = pd.read_json(file_name)
                    Styler.show_dataframe("DataFrame", df)
                except Exception as e:
                    st.warning(f"Error converting json to a dataframe ({e})")
            case _:
                st.code(
                    lines,
                    line_numbers=True,
                )
