from pathlib import Path


import pandas as pd
import streamlit as st

from streamlit.delta_generator import DeltaGenerator
from styler import Styler
from handlers.audiofile import AudioFile
from state import State
from zenmpd import ZenMPD


MUSIC_DIR = "/home/richard/Zen/Music/"


class MPD2:
    @staticmethod
    def convert_path(path: str) -> str:
        """Convert the MPD file path to the local music directory path."""
        return MUSIC_DIR + path

    @staticmethod
    def set_current_file() -> None:
        song = ZenMPD.get_currentsong()
        if lib_name := song.get("file"):
            State.set("current_folder", str(Path(MUSIC_DIR + lib_name).parent))
            State.set("current_file", MUSIC_DIR + lib_name)

    @staticmethod
    def _mpd_command(command: str, container: DeltaGenerator, **kwargs):
        match command:
            case "add":
                ZenMPD.add(kwargs["folder"])
                container.info(f"Added {kwargs['folder']}")
            case "replace":
                ZenMPD.replace(kwargs["folder"])
                container.info(f"Replacing with {kwargs['folder']}")
            case "play":
                ZenMPD.play()
                container.info("Play")
            case "pause":
                ZenMPD.pause()
                container.info("Pause")
            case "stop":
                ZenMPD.stop()
                container.info("Stop")
            case "previous":
                ZenMPD.previous()
                container.info("Previous")
            case "next":
                ZenMPD.next()
                container.info("Next")
            case "volup":
                ZenMPD.volup()
                container.info("Volume up")
            case "voldown":
                ZenMPD.voldown()
                container.info("Volume down")
            case "playrandomalbum":
                ZenMPD.playrandomalbum()
                container.info("Playing random album")
            case "addrandomalbum":
                ZenMPD.addrandomalbum()
                container.info("Adding random album")
            case "nowplaying":
                status, song, albumart = ZenMPD.nowplaying()
                cols = container.columns(2)
                with cols[0]:
                    data = {
                        "artist": song.get("artist"),
                        "Album": song.get("album"),
                        "Track": song.get("title"),
                        "File": song.get("file", ""),
                        "Progress": f"{status.get('elapsed')} / {song.get('duration')}",
                        "Position": song.get("pos", 0),
                        "Volume": status.get("volume", 0),
                        "State": status.get("state", "-"),
                    }
                    Styler.show_dict("Now Playing", data)
                with cols[1]:
                    if isinstance(albumart, str):
                        st.image(albumart, "Album Art")
                    elif "binary" in albumart:
                        image_bytes = albumart["binary"]
                        st.image(image_bytes, "Album Art")
                    else:
                        st.image(MUSIC_DIR + "default.png", "Album Art")
            case "playlist":
                playlist_info, current_id = ZenMPD.playlist()
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
    def _add_play_buttons(output_container: DeltaGenerator, folder: str):
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

    @staticmethod
    def add_playlist_buttons(output_container: DeltaGenerator, folder: str):
        cols = st.columns([1] * 7)
        short_folder = folder.replace(MUSIC_DIR, "")
        with cols[0]:
            st.markdown(f"📁 {short_folder}")

        Styler.add_button(
            cols[1],
            "Add",
            ":material/add_to_queue:",
            lambda: MPD2._mpd_command("add", output_container, folder=folder),
        )
        Styler.add_button(
            cols[2],
            "Replace",
            ":material/replace_audio:",
            lambda: MPD2._mpd_command("replace", output_container, folder=folder),
        )
        Styler.add_button(
            cols[3],
            "Play Random 🎲",
            ":material/album:",
            lambda: MPD2._mpd_command(
                "playrandomalbum", output_container, folder=folder
            ),
        )
        Styler.add_button(
            cols[4],
            "Add Random 🎲",
            ":material/album:",
            lambda: MPD2._mpd_command(
                "addrandomalbum", output_container, folder=folder
            ),
        )
        Styler.add_button(cols[5], "♻️", ":material/recycling:", lambda: None)
        Styler.add_button(
            cols[6], "Set as current", ":material/bolt:", MPD2.set_current_file
        )

    @staticmethod
    def show_actions(folder: str):
        with st.expander("🔊 MPD", expanded=True):
            # st.subheader(f"📁 {display_folder}")
            button_container = st.container()
            playlist_container = st.container()
            output_container = st.container()
            with button_container:
                MPD2._add_play_buttons(output_container, folder)
                MPD2.add_playlist_buttons(playlist_container, folder)
                tabs = st.tabs(["Now Playing", "Playlist", "Meta"])
                with tabs[0]:
                    MPD2._mpd_command("nowplaying", st.container())
                with tabs[1]:
                    MPD2._mpd_command("playlist", st.container())
                with tabs[2]:
                    if song_file := ZenMPD.get_currentsong().get("file"):
                        file_name = MUSIC_DIR + song_file
                        meta = AudioFile.get_mp3_meta(file_name)
                        Styler.show_dict("Metadata", meta)
                        id3 = AudioFile.get_id3_tag(file_name)
                        if id3:
                            Styler.show_dict("ID3 Tag", id3)
                        else:
                            st.warning(f"No ID3 data for {file_name}")
                    else:
                        st.warning("No song is currently playing.")
