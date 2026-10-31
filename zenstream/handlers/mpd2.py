from collections.abc import Generator
from contextlib import contextmanager
from os import listdir
from pathlib import Path
from random import choice

import pandas as pd
import streamlit as st
from mpd import MPDClient
from streamlit.delta_generator import DeltaGenerator
from styler import Styler
from handlers.audiofile import AudioFile
from state import State


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


class ZenMPD:
    @staticmethod
    def _get_library_files(folder: str, existing: list | None = None) -> list[str]:
        top_level = bool(existing is None)
        files = [] if top_level else existing
        for f in sorted(listdir(folder), reverse=False):
            file_path = Path("/".join([folder, f]))
            if file_path.is_dir():
                ZenMPD._get_library_files(str(file_path), existing=files)
            else:
                ext = f.split(".")[-1].lower()
                if ext in ["mp3", "flac", "wav", "m4a"]:
                    files.append(str(file_path))
        return [fname.replace(MUSIC_DIR, "") for fname in files]

    @staticmethod
    def add(folder: str):
        with get_mdp_client() as client:
            for lib_file in ZenMPD._get_library_files(folder):
                client.add(lib_file)

    @staticmethod
    def replace(folder: str):
        with get_mdp_client() as client:
            client.clear()
            for lib_file in ZenMPD._get_library_files(folder):
                client.add(lib_file)
            client.play(0)

    @staticmethod
    def play():
        with get_mdp_client() as client:
            status = client.status()
            if status.get("state") == "pause":
                client.pause(0)
            elif status.get("state") != "play":
                client.play(int(status.get("song", 0)))
        MPD2._paused = 0

    @staticmethod
    def pause():
        with get_mdp_client() as client:
            MPD2._paused = 1 - MPD2._paused
            client.pause(MPD2._paused)

    @staticmethod
    def stop():
        with get_mdp_client() as client:
            client.stop()
        MPD2._paused = 0

    @staticmethod
    def previous():
        with get_mdp_client() as client:
            pos = int(client.status().get("song", 0))
            client.play(max(pos - 1, 0))
        MPD2._paused = 0

    @staticmethod
    def next():
        with get_mdp_client() as client:
            status = client.status()
            pos = int(status.get("song", -1))
            if pos + 1 < int(status.get("playlistlength", 0)):
                client.play(pos + 1)
        MPD2._paused = 0

    @staticmethod
    def volup():
        with get_mdp_client() as client:
            status = client.status()
            volume = int(status.get("volume", 0))
            client.setvol(min(volume + 5, 100))

    @staticmethod
    def voldown():
        with get_mdp_client() as client:
            status = client.status()
            volume = int(status.get("volume", 0))
            client.setvol(max(volume - 5, 0))

    @staticmethod
    def _choose_random_album(client: MPDClient) -> str | None:
        all_files = client.listall("/")
        chosen, count = None, 0
        while count < 100 and not chosen:
            candidate = choice(all_files)
            if file_name := candidate.get("file"):
                chosen = file_name.split("/")
                chosen = MUSIC_DIR + "/".join(chosen[:-1])
            count += 1
        return chosen

    @staticmethod
    def playrandomalbum():
        with get_mdp_client() as client:
            if chosen := ZenMPD._choose_random_album(client):
                client.clear()
                for file_ in ZenMPD._get_library_files(chosen):
                    client.add(file_)
                client.play(0)

    @staticmethod
    def addrandomalbum():
        with get_mdp_client() as client:
            if chosen := ZenMPD._choose_random_album(client):
                for file_ in ZenMPD._get_library_files(chosen):
                    client.add(file_)

    @staticmethod
    def _get_folder_art(file_path: str) -> str | None:
        folder_path = Path(MUSIC_DIR + file_path).parent
        for file_name in folder_path.iterdir():
            if file_name.is_file() and file_name.name.lower().endswith(
                (".jpg", ".jpeg", ".png")
            ):
                return str(file_name)
        return None

    @staticmethod
    def nowplaying() -> dict | str | None:
        with get_mdp_client() as client:
            status = client.status()
            song = client.currentsong()
            file_ = song.get("file", "")
            if file_ and Path(file_).exists():
                albumart = client.albumart(file_)
            else:
                albumart = ZenMPD._get_folder_art(file_)
        return status, song, albumart

    @staticmethod
    def playlist() -> tuple[list[dict], str | None]:
        with get_mdp_client() as client:
            playlist_info = client.playlistinfo()
            current_id = client.currentsong().get("id")
        return playlist_info, current_id

    @staticmethod
    def get_status() -> dict:
        with get_mdp_client() as client:
            return client.status()

    @staticmethod
    def get_currentsong() -> dict:
        with get_mdp_client() as client:
            return client.currentsong()


class MPD2:
    _paused = 0

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
