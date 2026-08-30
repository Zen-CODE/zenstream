import webbrowser
from functools import partial
from os import listdir, sep
from os.path import join
from pathlib import Path
from uuid import uuid4

import pyperclip
import streamlit as st
from actions import Action
from handlers.filedetails import FileDetails
from state import State
from streamlit.delta_generator import DeltaGenerator

from styler import NUM_COLUMNS, Styler
from handlers.edit import EditFile


class ZenStream:
    @staticmethod
    def header():
        with st.container():
            col1, col2 = st.columns([0.96, 0.04])
            col1.title("💧 ZenStream")
            col2.image("images/favicon.png")

    @staticmethod
    def add_path():
        with st.container():
            ZenStream._add_path_buttons()

    @staticmethod
    def _add_path_buttons():
        folder = State.get("current_folder", str(Path.cwd()))
        parts = folder.split(sep)[1:]
        num_folders = len(parts)

        cols = st.columns(num_folders + 2)  # Add root folder and info tag
        cols[0].info("💧💧 Current folder")
        cols[1].button(
            "📁/",
            key=str(uuid4()),
            width="stretch",
            on_click=partial(State.set, "current_folder", "/"),
        )
        if num_folders == 1 and parts[0] == "":
            return

        dest_folder = ""
        for i in range(num_folders):
            dest_folder = dest_folder + sep + parts[i]
            cols[i + 2].button(
                "📁 " + parts[i],
                key=str(uuid4()),
                width="stretch",
                on_click=partial(State.set, "current_folder", dest_folder),
            )

    @staticmethod
    def _add_folder_button(container: DeltaGenerator, text: str, folder: str):
        Styler.add_button(
            container,
            "📁 " + text,
            None,
            lambda: State.set("current_folder", folder),
        )

    @staticmethod
    def _add_file_button(container: DeltaGenerator, file_name: str, folder: str):
        if sep.join([folder, file_name]) == State.get("current_file"):
            text = file_name + " 🟢"
        else:
            text = file_name
        Styler.add_button(
            container,
            text,
            Action.get_icon(file_name),
            lambda: State.set("current_file", sep.join([folder, file_name])),
        )

    @staticmethod
    def listing():
        def split_list(lst: list, x_parts: int) -> list:
            # Calculate the base size and the remainder
            n = len(lst)
            size = n // x_parts
            remainder = n % x_parts

            result = []
            start = 0
            for i in range(x_parts):
                # Add 1 to the size of the first 'remainder' chunks
                end = start + size + (1 if i < remainder else 0)
                result.append(lst[start:end])
                start = end

            return result

        folder = State.get("current_folder", str(Path.cwd()))
        with st.expander("💧💧 Folder contents", expanded=True):
            cols = st.columns(NUM_COLUMNS)
            file_list = sorted(listdir(folder))
            list_of_columns = split_list(file_list, NUM_COLUMNS)
            for i, column in enumerate(list_of_columns):
                for file_name in column:
                    final_path = Path(join(folder, file_name))
                    if final_path.is_dir():
                        ZenStream._add_folder_button(
                            cols[i], file_name, str(final_path)
                        )
                    else:
                        ZenStream._add_file_button(cols[i], file_name, folder)

    @staticmethod
    def _confirm_delete(file_name: str):
        st.warning("⚠️ Are you sure you want to delete this file?")
        col_yes, col_no = st.columns(2)
        Styler.add_button(
            col_yes,
            "Delete",
            ":material/delete:",
            lambda *args: Action.delete_file(file_name),
            width="content",
        )
        Styler.add_button(
            col_no,
            "Cancel",
            ":material/close:",
            on_click=lambda *args: State.set("delete_file", ""),
            type="primary",
            width="content",
        )

    @staticmethod
    def _show_file_buttons(file_name: str):
        # Add buttons for Open, Copy, Delete and Clear
        col1, col2, col3, col4, col5 = st.columns([1] * 5)

        Styler.add_button(
            col1,
            "Copy path",
            on_click=lambda *args: pyperclip.copy(file_name),
            icon=":material/content_copy:",
        )
        Styler.add_button(
            col2,
            "Open",
            on_click=lambda *args: webbrowser.open(file_name),
            icon=":material/open_in_full:",
        )
        Styler.add_link_button(
            col3,
            "Edit",
            link=f"/?file_name={file_name}",
            icon=":material/edit:",
        )
        Styler.add_button(
            col4,
            "Delete",
            on_click=lambda *args: State.set("delete_file", file_name),
            icon=":material/delete:",
        )
        Styler.add_button(
            col5,
            "Clear",
            on_click=lambda *args: State.set("current_file", ""),
            icon=":material/delete:",
        )

    @staticmethod
    def details(file_name):
        if del_file := State.get("delete_file"):
            ZenStream._confirm_delete(del_file)
        ZenStream._show_file_buttons(file_name)

        for handler in Action.get_handlers(file_name):
            handler.show_file(file_name)

        with st.expander("❄️ Details", expanded=True):
            FileDetails.show_file(file_name)

    @staticmethod
    def show_footer():
        st.markdown('“Be like water..." - *Bruce Lee*')

    @staticmethod
    def show():
        ZenStream.header()
        if file_name := st.query_params.get("file_name"):
            EditFile.edit_file(file_name)
        else:
            ZenStream.add_path()
            with st.spinner("Loading folder..."):
                ZenStream.listing()
                if file_name := State.get("current_file"):
                    with st.expander(
                        f"💧💧💧 Current file: {file_name}", expanded=True
                    ):
                        ZenStream.details(file_name)
            ZenStream.show_footer()


if __name__ == "__main__":
    if file_name := st.query_params.get("file_name"):
        file_ending = Path(file_name).name
        st.set_page_config(
            page_title=f"{file_ending} - ZenStream",
            page_icon="images/favicon.png",
            layout="wide",
        )
    else:
        st.set_page_config(
            page_title="ZenStream", page_icon="images/favicon.png", layout="wide"
        )

    State.load()
    ZenStream.show()
