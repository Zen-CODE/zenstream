import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from styler import Styler
from actions import Action
import subprocess
from pathlib import Path
from utils import get_ext


class PythonHandler:
    @staticmethod
    def _run(file_name: str):
        """Run the Python file."""
        file_path = Path(file_name).parent
        return subprocess.run(
            ["python", file_name], capture_output=True, text=True, cwd=file_path
        )

    @staticmethod
    def add_buttons(
        container: DeltaGenerator, file_name: str, output_box: DeltaGenerator
    ):
        """Add action buttons for the given file."""
        col1, col2 = container.columns([0.5, 0.5])

        col2.checkbox("Load env file", value=True)
        print("Adding buttons")
        Styler.add_button(
            col1,
            "Run",
            Action.get_icon(file_name),
            on_click=lambda: PythonHandler.run_file(file_name, output_box),
        )

    @staticmethod
    def run_file(file_name: str, container: DeltaGenerator) -> None:
        """Run the specified file"""

        with container.spinner(f"Running {file_name}"):
            result = PythonHandler._run(file_name)

            print(f"Ran : results - {result}")
            if result.returncode == 0:
                container.markdown("**✅ Output**")
                container.code(result.stdout)
            else:
                container.subheader("**⚠️ Error**")
                container.code(result.stderr)


class EditFile:
    @staticmethod
    def _load_text(file_name: str) -> str:
        """Load the file content into a string and return it."""
        try:
            with open(file_name, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            st.warning(f"Unable to read the file...({e})")

        return ""

    @staticmethod
    def _save_text(file_name: str, text_area: str, container: DeltaGenerator):
        """Save the text to the file."""
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(text_area)
            container.success("File saved successfully!")
        except Exception as e:
            container.warning(f"Unable to save the file...({e})")

    @staticmethod
    def _run_file(file_name: str, container: DeltaGenerator) -> None:
        """Run the specified file"""

        with container.spinner(f"Running {file_name}"):
            match get_ext(file_name):
                case "sh":
                    result = subprocess.run(
                        ["sh", file_name], capture_output=True, text=True
                    )
                case _:
                    container.warning(f"Unrecognized file type: {file_name}")
                    return
            if result.returncode == 0:
                container.markdown("**✅ Output**")
                container.code(result.stdout)
            else:
                container.subheader("**⚠️ Error**")
                container.code(result.stderr)

    @staticmethod
    def edit_file(file_name: str):
        """Display the file details."""
        text = EditFile._load_text(file_name)
        ext = get_ext(file_name)
        button_box = st.container()
        output_box = st.container()

        match ext:
            case "py":
                col1, col2 = button_box.columns([0.5, 0.5])
                PythonHandler.add_buttons(col2, file_name, output_box)
            case _:
                col1 = button_box

        text_area = button_box.text_area(f"{file_name}", value=text, height=250)

        Styler.add_button(
            col1,
            "Save",
            ":material/save:",
            on_click=lambda: EditFile._save_text(file_name, text_area, output_box),
        )
