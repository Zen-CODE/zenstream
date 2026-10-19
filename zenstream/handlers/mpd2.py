import streamlit as st
from styler import Styler
from streamlit.delta_generator import DeltaGenerator
from mpd import MPDClient
from contextlib import contextmanager
from collections.abc import Generator

MUSIC_DIR = "/home/richard/Zen/Music/"


@contextmanager
def get_mdp_client() -> Generator[MPDClient, None, None]:
    try:
        client = MPDClient()
        client.connect("localhost", 6600)
        yield client

    finally:
        try:
            client.close()
            client.disconnect()
        except Exception:
            st.error("Error unloading MDPClient: {e}")


class MPD2:
    @staticmethod
    def _mpd_command(command: str, container: DeltaGenerator, **kwargs):
        match command:
            case "add" | "replace":
                # folder = Path(kwargs["folder"])
                # files = [file_path.name for file_path in folder.iterdir()
                #          if file_path.name.endswith(
                #              (".mp3", ".flac", ".wav", ".ogg", ".wma"))]
                # file_names = sorted([file_path.replace(MUSIC_DIR, "")
                #                      for file_path in files])

                with get_mdp_client() as client:
                    if command == "replace":
                        client.clear()
                    rel_folder = kwargs["folder"].replace(MUSIC_DIR, "")
                    client.add(rel_folder)
                    # for file_name in file_names:
                    #     client.add(file_name)

            case "play":
                with get_mdp_client() as client:
                    client.play(0)
                with container:
                    st.info("Play")

            case "pause":
                with get_mdp_client() as client:
                    client.pause(0)
                with container:
                    st.info("Pause")
            case "stop":
                with get_mdp_client() as client:
                    client.stop()
                with container:
                    st.info("Stop")
            case "previous":
                with get_mdp_client() as client:
                    client.previous()
                with container:
                    st.info("Previous")
            case "next":
                with get_mdp_client() as client:
                    client.next()
                with container:
                    st.info("Volume up")

            case "volup":
                with get_mdp_client() as client:
                    status = client.status()
                    volume = int(status.get("volume", 0))
                    client.setvol(min(volume + 5, 100))
                with container:
                    st.info("Volume up")

            case "voldown":
                with get_mdp_client() as client:
                    status = client.status()
                    volume = int(status.get("volume", 0))
                    client.setvol(max(volume - 5, 0))
                with container:
                    st.info("Volume down")

            case "nowplaying":
                with get_mdp_client() as client:
                    status = client.status()
                with container:
                    data = {
                        "Volume": status["volume"],
                        "State": status["state"],
                        "Elapsed": status.get("elapsed", 0),
                        "Playlist no.": status.get("playlist", 0),
                        "Playlist length": status.get("playlistlength", 0),
                    }

                    Styler.show_dict("Now playing", data)

            case "playlist":
                with get_mdp_client() as client:
                    playlist = client.playlist()
                with container:
                    disp_dict = {f"Item {k}": item for k, item in enumerate(playlist)}
                    Styler.show_dict("Playlist", disp_dict)

    @staticmethod
    def _add_play_button(output_container: DeltaGenerator):
        cols = st.columns([1] * 7)

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
            "Play",
            ":material/play_arrow:",
            lambda: MPD2._mpd_command("play", output_container),
        )
        Styler.add_button(
            cols[3],
            "Pause",
            ":material/pause:",
            lambda: MPD2._mpd_command("pause", output_container),
        )
        Styler.add_button(
            cols[4],
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
            cols[6],
            "Vol down",
            ":material/volume_down:",
            lambda: MPD2._mpd_command("voldown", output_container),
        )

    @staticmethod
    def _add_other_commands(output_container: DeltaGenerator, folder: str):
        cols = st.columns([1] * 4)

        Styler.add_button(
            cols[0],
            "Add folder",
            ":material/add_to_queue:",
            lambda: MPD2._mpd_command("add", output_container, folder=folder),
        )
        Styler.add_button(
            cols[1],
            "Replace",
            ":material/replace_audio:",
            lambda: MPD2._mpd_command("replace", output_container, folder=folder),
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
    def show_actions(folder: str):
        with st.expander("🔊 MPD", expanded=True):
            st.subheader("Music Player Daemon 2")
            button_container = st.container()
            output_container = st.container()
            with button_container:
                MPD2._add_play_button(output_container)
                MPD2._add_other_commands(output_container, folder)
