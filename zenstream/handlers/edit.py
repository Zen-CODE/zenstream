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
    def _find_env_file(file_path: Path) -> Path | None:
        """Search current and parent folders until a .env or .env.local file
        is found and return its path, or None if not found."""
        current = file_path.parent

        for directory in [current, *current.parents]:
            for name in [".env", ".env.local"]:
                candidate = directory / name
                if candidate.is_file():
                    return candidate
        return None

    @staticmethod
    def parse_env_file(file_path: Path) -> dict[str, str]:
        """Parse a .env / .env.local file into a dictionary."""
        env_vars: dict[str, str] = {}
        try:
            with open(file_path, encoding="utf-8") as f:
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
            st.warning(f"Error reading env file {file_path}: {e}")
        return env_vars

    @staticmethod
    def _get_environment(
        file_path: Path, load_env: bool = True
    ) -> tuple[dict[str, str]]:
        """Return the current evironment, along with any loaded env files."""
        env = os.environ.copy()
        if load_env:
            env_file = PythonHandler._find_env_file(file_path.parent)
            if env_file:
                env.update(PythonHandler._parse_env_file(env_file))
        return env

    @staticmethod
    def _get_venv(file_path: Path) -> Path | None:
        """Return the path to the virtual env executable or None."""
        current = file_path.parent
        for directory in [current, *current.parents]:
            for name in [".env", ".venv"]:
                candidate = directory / name
                if candidate.is_dir():
                    if sys.platform == "win32":
                        python_bin = candidate / "Scripts" / "python.exe"
                    else:
                        python_bin = candidate / "bin" / "python"
                    if python_bin.exists():
                        return python_bin
        return None

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
    def _run(file_path: Path, env: dict[str, str] | None = None):
        """Run the Python file capturing output."""
        python_bin = PythonHandler._get_python_binary(file_path)
        return subprocess.run(
            [str(python_bin), str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent,
            env=env,
        )

    @staticmethod
    def _get_python_binary(file_path: Path) -> Path | None:
        """Return the appropriate python binary to run"""
        if python_bin := PythonHandler._get_venv(file_path):
            return python_bin
        return sys.executable or "python3"

    @staticmethod
    def _run_in_terminal(file_path: Path, env: dict[str, str] | None = None):
        """Run the Python file in a new terminal window."""
        python_bin = PythonHandler._get_python_binary(file_path)
        return PythonHandler._launch_terminal(
            [str(python_bin), str(file_path)],
            cwd=file_path.parent,
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
        file_path = Path(file_name).resolve()
        env = PythonHandler._get_environment(file_path, load_env=load_env)

        if new_terminal:
            try:
                PythonHandler._run_in_terminal(file_path, env=env)
                container.success(f"Launched {file_path.name} in a new terminal.")
            except Exception as e:
                container.error(f"Failed to launch in new terminal: {e}")
            return
        else:
            with container.spinner(f"Running {file_path}"):
                result = PythonHandler._run(file_path, env=env)
                print(f"Ran : results - {result}")
                if result.returncode == 0:
                    container.markdown("**✅ Output**")
                    container.code(
                        result.stdout if result.stdout else f"Error {result.stderr}"
                    )
                else:
                    container.subheader("**⚠️ Error**")
                    container.code(
                        result.stderr if result.stderr else "(No error output)"
                    )


class ShellHandler:
    @staticmethod
    def _run(file_path: Path):
        """Run the shell file."""
        return subprocess.run(
            ["sh", str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent,
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
            file_path = Path(file_name)
            result = ShellHandler._run(file_path)
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
