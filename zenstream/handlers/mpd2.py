import pandas as pd
import streamlit as st
from styler import Styler
from streamlit.delta_generator import DeltaGenerator
from mpd import MPDClient
from contextlib import contextmanager
from collections.abc import Generator
from random import choice


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
    _paused = 0

    @staticmethod
    def convert_path(path: str) -> str:
        """Convert the MPD file path to the local music directory path."""
        return MUSIC_DIR + path

    @staticmethod
    def _mpd_command(command: str, container: DeltaGenerator, **kwargs):
        match command:
            case "add" | "replace":
                with get_mdp_client() as client:
                    if command == "replace":
                        client.clear()
                    rel_folder = kwargs["folder"].replace(MUSIC_DIR, "")
                    client.add(rel_folder)

            case "play":
                with get_mdp_client() as client:
                    status = client.status()
                    if status.get("state") == "pause":
                        client.pause(0)
                    elif status.get("state") != "play":
                        client.play(int(status.get("song", 0)))
                MPD2._paused = 0
                with container:
                    st.info("Play")

            case "pause":
                with get_mdp_client() as client:
                    MPD2._paused = 1 - MPD2._paused
                    client.pause(MPD2._paused)
                with container:
                    st.info("Pause")
            case "stop":
                with get_mdp_client() as client:
                    client.stop()
                with container:
                    st.info("Stop")
            case "previous":
                with get_mdp_client() as client:
                    pos = int(client.status().get("song", 0))
                    client.play(max(pos - 1, 0))
                MPD2._paused = 0
                with container:
                    st.info("Previous")
            case "next":
                with get_mdp_client() as client:
                    status = client.status()
                    pos = int(status.get("song", -1))
                    if pos + 1 < int(status.get("playlistlength", 0)):
                        client.play(pos + 1)
                MPD2._paused = 0
                with container:
                    st.info("Next")

            case "volup":
                with get_mdp_client() as client:
                    status = client.status()
                    volume = int(status.get("volume", 0))
                    client.setvol(min(volume + 5, 100))
                with container:
                    st.info("Volume up")
            case "playrandomalbum" | "addrandomalbum":
                with get_mdp_client() as client:
                    all_files = client.listall("/")
                    chosen, count = None, 0
                    while count < 100 and not chosen:
                        candidate = choice(all_files)
                        if file_name := candidate.get("file"):
                            chosen = file_name.split("/", maxsplit=2)
                            chosen = "/".join(chosen)
                        count += 1
                    if chosen:
                        if command == "playrandomalbum":
                            client.clear()
                            client.add(chosen)
                            client.play(0)
                        elif command == "addrandomalbum":
                            client.add(chosen)

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
                    song = client.currentsong()
                    file_ = song.get("file", "")
                    if file_:
                        albumart = client.albumart(song.get("file", ""))
                    else:
                        albumart = None

                cols = container.columns(2)
                with cols[0]:
                    product_data = {
                        "🟢": [
                            ":blue[Artist]",
                            ":blue[Album]",
                            ":blue[Track]",
                            ":blue[File]",
                            ":blue[Progress]",
                            ":blue[Position]",
                            ":blue[Volume]",
                            ":blue[State]",
                            ":blue[ID]",
                        ],
                        "": [
                            song.get("artist"),
                            song.get("album"),
                            song.get("title"),
                            song.get("file", ""),
                            str(
                                100
                                * float(status.get("elapsed", 0))
                                / float(song.get("duration", 1))
                                if song.get("duration")
                                else 0
                            ),
                            song.get("pos", 0),
                            status.get("volume", 0),
                            status.get("state", "-"),
                            song.get("id", 0),
                        ],
                    }
                    st.table(product_data, border="horizontal")
                with cols[1]:
                    if albumart and "binary" in albumart:
                        image_bytes = albumart["binary"]
                        st.image(image_bytes, "Album Art")
                    else:
                        st.image(MUSIC_DIR + "default.png", "Album Art")

            case "playlist":
                with get_mdp_client() as client:
                    playlist_info = client.playlistinfo()
                    current_id = client.currentsong().get("id")

                ids = [item.get("id") for item in playlist_info]
                playlist_data = {
                    "🟢": ["▶" if item_id == current_id else "" for item_id in ids],
                    "Pos": [item.get("pos", "") for item in playlist_info],
                    "Artist": [item.get("artist", "") for item in playlist_info],
                    "Album": [item.get("album", "") for item in playlist_info],
                    "Title": [item.get("title", "") for item in playlist_info],
                    "ID": ids,
                }

                def _highlight_current(row):
                    style = (
                        "background-color: rgba(0, 160, 80, 0.25)"
                        if row["ID"] == current_id
                        else ""
                    )
                    return [style] * len(row)

                with container:
                    df = pd.DataFrame(playlist_data)
                    st.table(df.style.apply(_highlight_current, axis=1))

    @staticmethod
    def _add_play_button(output_container: DeltaGenerator, folder: str):
        cols = st.columns([1] * 11)

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
            "🔉",
            ":material/volume_down:",
            lambda: MPD2._mpd_command("voldown", output_container),
        )

        Styler.add_button(
            cols[6],
            "🔊",
            ":material/volume_up:",
            lambda: MPD2._mpd_command("volup", output_container),
        )

        Styler.add_button(
            cols[7],
            "Add ➕",
            ":material/add_to_queue:",
            lambda: MPD2._mpd_command("add", output_container, folder=folder),
        )
        Styler.add_button(
            cols[8],
            "Replace ❇️",
            ":material/replace_audio:",
            lambda: MPD2._mpd_command("replace", output_container, folder=folder),
        )
        Styler.add_button(
            cols[9],
            "Play Random 🎲",
            ":material/album:",
            lambda: MPD2._mpd_command(
                "playrandomalbum", output_container, folder=folder
            ),
        )
        Styler.add_button(
            cols[10],
            "Add Random 🎲",
            ":material/album:",
            lambda: MPD2._mpd_command(
                "addrandomalbum", output_container, folder=folder
            ),
        )

    @staticmethod
    def show_actions(folder: str):
        # display_folder = folder.replace(MUSIC_DIR, "")
        with st.expander("🔊 MPD", expanded=True):
            # st.subheader(f"📁 {display_folder}")
            button_container = st.container()
            output_container = st.container()
            with button_container:
                MPD2._add_play_button(output_container, folder)
                tabs = st.tabs(["Now Playing", "Playlist"])
                with tabs[0]:
                    MPD2._mpd_command("nowplaying", st.container())
                with tabs[1]:
                    MPD2._mpd_command("playlist", st.container())
