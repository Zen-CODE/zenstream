import streamlit as st
from styler import Styler
from streamlit.delta_generator import DeltaGenerator


class MPD2:
    @staticmethod
    def _mpd_command(command: str, container: DeltaGenerator):
        container.info(f"MPD2: Command fired - {command}")

    @staticmethod
    def _add_play_button():
        output_container = st.container()
        cols = st.columns([1] * 6)

        Styler.add_button(
            cols[0],
            "Previous",
            ":material/keyboard_double_arrow_left:",
            lambda: MPD2._mpd_command("previous", output_container),
        )
        Styler.add_button(
            cols[1],
            "Stop",
            ":material/stop:",
            lambda: MPD2._mpd_command("stop", output_container),
        )
        Styler.add_button(
            cols[2],
            "Play/Pause",
            ":material/play_pause:",
            lambda: MPD2._mpd_command("playpause", output_container),
        )
        Styler.add_button(
            cols[3],
            "Next",
            ":material/keyboard_double_arrow_right:",
            lambda: MPD2._mpd_command("next", output_container),
        )

        Styler.add_button(
            cols[5],
            "Vol up",
            ":material/volume_up:",
            lambda: MPD2._mpd_command("volup", output_container),
        )
        Styler.add_button(
            cols[4],
            "Vol down",
            ":material/volume_down:",
            lambda: MPD2._mpd_command("voldown", output_container),
        )

    @staticmethod
    def _add_other_commands():
        output_container = st.container()
        cols = st.columns([1] * 4)

        Styler.add_button(
            cols[0],
            "Add folder",
            ":material/add_to_queue:",
            lambda: MPD2._mpd_command("add", output_container),
        )
        Styler.add_button(
            cols[1],
            "Replace",
            ":material/replace_audio:",
            lambda: MPD2._mpd_command("replace", output_container),
        )
        Styler.add_button(
            cols[2],
            "Now PLaying",
            ":material/info:",
            lambda: MPD2._mpd_command("nowplaying", output_container),
        )
        Styler.add_button(
            cols[3],
            "Show playlist",
            ":material/playlist_play:",
            lambda: MPD2._mpd_command("playlist", output_container),
        )

    @staticmethod
    def show_actions():
        with st.expander("🔊 MPD", expanded=True):
            st.subheader("Music Player Daemon 2")
            MPD2._add_play_button()
            MPD2._add_other_commands()
