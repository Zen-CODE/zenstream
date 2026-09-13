import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import streamlit as st
from actions import Action
from streamlit.delta_generator import DeltaGenerator
from styler import Styler
from utils import get_ext


class PythonHandler:
    @staticmethod
    def find_env_file(start_path: Path) -> Path | None:
        """Search current and parent folders until a .env or .env.local file
        is found and return its path, or None if not found."""
        current = start_path.resolve()
        if current.is_file():
            current = current.parent

        for directory in [current, *current.parents]:
            for name in [".env", ".env.local"]:
                candidate = directory / name
                if candidate.is_file():
                    return candidate
        return None

    @staticmethod
    def parse_env_file(path: Path) -> dict[str, str]:
        """Parse a .env / .env.local file into a dictionary."""
        env_vars: dict[str, str] = {}
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("export "):
                        line = line[len("export ") :].strip()
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip()
                        if len(val) >= 2 and (
                            (val.startswith('"') and val.endswith('"'))
                            or (val.startswith("'") and val.endswith("'"))
                        ):
                            val = val[1:-1]
                        env_vars[key] = val
        except Exception as e:
            st.warning(f"Error reading env file {path}: {e}")
        return env_vars

    @staticmethod
    def get_environment(file_name: str, load_env: bool = True) -> tuple[dict[str, str]]:
        """Return the current evironment, along with any loaded env files."""
        env = os.environ.copy()
        if load_env:
            env_file = PythonHandler.find_env_file(Path(file_name).parent)
            if env_file:
                env.update(PythonHandler.parse_env_file(env_file))
        return env

    @staticmethod
    def _launch_terminal(
        args: list[str], cwd: Path | str, env: dict[str, str] | None = None
    ) -> subprocess.Popen:
        """Launch a command in a new terminal emulator window."""
        system = platform.system()
        if system == "Windows":
            cmd_str = subprocess.list2cmdline(args)
            return subprocess.Popen(
                f'start cmd.exe /k "{cmd_str}"',
                shell=True,
                cwd=cwd,
                env=env,
            )
        elif system == "Darwin":
            cmd_str = shlex.join(args)
            escaped_cmd = cmd_str.replace("\\", "\\\\").replace('"', '\\"')
            apple_script = f'tell application "Terminal" to do script "{escaped_cmd}"'
            return subprocess.Popen(["osascript", "-e", apple_script], cwd=cwd, env=env)
        else:
            terminals = [
                "x-terminal-emulator",
                "konsole",
                "gnome-terminal",
                "xfce4-terminal",
                "kitty",
                "alacritty",
                "terminator",
                "xterm",
            ]
            term = next((t for t in terminals if shutil.which(t)), None)
            if not term:
                raise RuntimeError("No supported terminal emulator found.")

            shell_bin = shutil.which("bash") or shutil.which("sh") or "sh"
            pause_cmd = (
                'read -p "Press Enter to exit..."'
                if "bash" in shell_bin
                else 'printf "Press Enter to exit..."; read -r _'
            )
            cmd_str = shlex.join(args)
            inner_cmd = f"{cmd_str}; echo; {pause_cmd}"

            if term == "gnome-terminal":
                term_cmd = [term, "--", shell_bin, "-c", inner_cmd]
            elif term == "konsole":
                term_cmd = [term, "--noclose", "-e", shell_bin, "-c", inner_cmd]
            else:
                term_cmd = [term, "-e", shell_bin, "-c", inner_cmd]

            return subprocess.Popen(term_cmd, cwd=cwd, env=env)

    @staticmethod
    def _run(file_name: str, env: dict[str, str] | None = None):
        """Run the Python file capturing output."""
        resolved_path = Path(file_name).resolve()
        file_path = resolved_path.parent
        python_bin = sys.executable or "python3"
        return subprocess.run(
            [python_bin, str(resolved_path)],
            capture_output=True,
            text=True,
            cwd=file_path,
            env=env,
        )

    @staticmethod
    def _run_in_terminal(file_name: str, env: dict[str, str] | None = None):
        """Run the Python file in a new terminal window."""
        file_path = Path(file_name).resolve().parent
        python_bin = sys.executable or "python3"
        return PythonHandler._launch_terminal(
            [python_bin, str(Path(file_name).resolve())],
            cwd=file_path,
            env=env,
        )

    @staticmethod
    def add_buttons(
        container: DeltaGenerator, file_name: str, output_box: DeltaGenerator
    ):
        """Add action buttons for the given file."""
        with container.form(key=f"python_form_{file_name}"):
            col_run, col_env, col_term = st.columns([1] * 3)
            with col_run:
                submitted = st.form_submit_button(
                    "Run",
                    icon=Action.get_icon(file_name),
                )
            with col_env:
                load_env = st.checkbox("Load env file", value=True)
            with col_term:
                new_terminal = st.checkbox("New terminal", value=False)

            if submitted:
                PythonHandler.run_file(
                    file_name,
                    output_box,
                    load_env=load_env,
                    new_terminal=new_terminal,
                )

    @staticmethod
    def run_file(
        file_name: str,
        container: DeltaGenerator,
        load_env: bool = True,
        new_terminal: bool = False,
    ) -> None:
        """Run the specified python file."""
        env = PythonHandler.get_environment(file_name, load_env=load_env)

        if new_terminal:
            try:
                PythonHandler._run_in_terminal(file_name, env=env)
                container.success(f"Launched {Path(file_name).name} in a new terminal.")
            except Exception as e:
                container.error(f"Failed to launch in new terminal: {e}")
            return
        else:
            with container.spinner(f"Running {file_name}"):
                result = PythonHandler._run(file_name, env=env)
                print(f"Ran : results - {result}")
                if result.returncode == 0:
                    container.markdown("**✅ Output**")
                    container.code(result.stdout if result.stdout else "(No output)")
                else:
                    container.subheader("**⚠️ Error**")
                    container.code(
                        result.stderr if result.stderr else "(No error output)"
                    )


class ShellHandler:
    @staticmethod
    def _run(file_name: str):
        """Run the shell file."""
        resolved_path = Path(file_name).resolve()
        file_path = resolved_path.parent
        return subprocess.run(
            ["sh", str(resolved_path)],
            capture_output=True,
            text=True,
            cwd=file_path,
        )

    @staticmethod
    def add_buttons(
        container: DeltaGenerator, file_name: str, output_box: DeltaGenerator
    ):
        """Add action buttons for the given file."""
        with container.form(key=f"shell_form_{file_name}"):
            submitted = st.form_submit_button(
                "Run",
                icon=Action.get_icon(file_name),
            )
            if submitted:
                ShellHandler.run_file(file_name, output_box)

    @staticmethod
    def run_file(file_name: str, container: DeltaGenerator) -> None:
        """Run the specified file"""
        with container.spinner(f"Running {file_name}"):
            result = ShellHandler._run(file_name)
            print(f"Ran : results - {result}")
            if result.returncode == 0:
                container.markdown("**✅ Output**")
                container.code(result.stdout if result.stdout else "(No output)")
            else:
                container.subheader("**⚠️ Error**")
                container.code(result.stderr if result.stderr else "(No error output)")


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
    def edit_file(file_name: str):
        """Display the file details."""
        text = EditFile._load_text(file_name)
        ext = get_ext(file_name)
        button_box = st.container()
        output_box = st.container()

        match ext:
            case "py":
                col1, col2 = button_box.columns([0.25, 0.75])
                PythonHandler.add_buttons(col2, file_name, output_box)
            case "sh":
                col1, col2 = button_box.columns([0.25, 0.75])
                ShellHandler.add_buttons(col2, file_name, output_box)
            case _:
                col1 = button_box

        text_area = button_box.text_area(f"{file_name}", value=text, height=250)

        Styler.add_button(
            col1,
            "Save",
            ":material/save:",
            on_click=lambda: EditFile._save_text(file_name, text_area, output_box),
        )
