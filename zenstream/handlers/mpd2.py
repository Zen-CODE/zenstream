from pathlib import Path

import pandas as pd
import streamlit as st
from styler import Styler
from streamlit.delta_generator import DeltaGenerator
from mpd import MPDClient
from contextlib import contextmanager
from collections.abc import Generator
from random import choice
from os import listdir, path


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
    def _get_library_files(folder: str) -> list[str] | None:
        files = []
        lib_folder = folder.replace(MUSIC_DIR, "")
        for f in sorted(listdir(folder), reverse=False):
            ext = f.split(".")[-1].lower()
            if ext in ["mp3", "flac", "wav", "m4a"]:
                files.append(path.join(lib_folder, f))
        return files if files else None

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
                chosen = file_name.split("/", maxsplit=2)
                chosen = "/".join(chosen)
            count += 1
        return chosen

    @staticmethod
    def playrandomalbum():
        with get_mdp_client() as client:
            if chosen := ZenMPD._choose_random_album(client):
                client.clear()
                client.add(chosen)
                client.play(0)

    @staticmethod
    def addrandomalbum():
        with get_mdp_client() as client:
            if chosen := ZenMPD._choose_random_album(client):
                client.add(chosen)

    @staticmethod
    def nowplaying() -> dict | str | None:
        with get_mdp_client() as client:
            status = client.status()
            song = client.currentsong()
            file_ = song.get("file", "")
            if file_ and Path(file_).exists():
                albumart = client.albumart(file_)
            else:
                albumart = None
        return status, song, albumart

    @staticmethod
    def playlist() -> tuple[list[dict], str | None]:
        with get_mdp_client() as client:
            playlist_info = client.playlistinfo()
            current_id = client.currentsong().get("id")
        return playlist_info, current_id


class MPD2:
    _paused = 0

    @staticmethod
    def convert_path(path: str) -> str:
        """Convert the MPD file path to the local music directory path."""
        return MUSIC_DIR + path

    @staticmethod
    def _mpd_command(command: str, container: DeltaGenerator, **kwargs):
        match command:
            case "add":
                ZenMPD.add(kwargs["folder"])
            case "replace":
                ZenMPD.replace(kwargs["folder"])
            case "play":
                ZenMPD.play()
                container.info("Play")
            case "pause":
                ZenMPD.pause()
                container.info("Pause")
            case "stop":
                ZenMPD.stop()
                with container:
                    st.info("Stop")
            case "previous":
                ZenMPD.previous()
                with container:
                    st.info("Previous")
            case "next":
                ZenMPD.next()
                with container:
                    st.info("Next")
            case "volup":
                ZenMPD.volup()
                with container:
                    st.info("Volume up")
            case "voldown":
                ZenMPD.voldown()
                with container:
                    st.info("Volume down")
            case "playrandomalbum":
                ZenMPD.playrandomalbum()
            case "addrandomalbum":
                ZenMPD.addrandomalbum()
            case "nowplaying":
                status, song, albumart = ZenMPD.nowplaying()
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
        cols = st.columns([1] * 5)

        Styler.add_button(
            cols[0],
            "Add ➕",
            ":material/add_to_queue:",
            lambda: MPD2._mpd_command("add", output_container, folder=folder),
        )
        Styler.add_button(
            cols[1],
            "Replace ❇️",
            ":material/replace_audio:",
            lambda: MPD2._mpd_command("replace", output_container, folder=folder),
        )
        Styler.add_button(
            cols[2],
            "Play Random 🎲",
            ":material/album:",
            lambda: MPD2._mpd_command(
                "playrandomalbum", output_container, folder=folder
            ),
        )
        Styler.add_button(
            cols[3],
            "Add Random 🎲",
            ":material/album:",
            lambda: MPD2._mpd_command(
                "addrandomalbum", output_container, folder=folder
            ),
        )
        Styler.add_button(cols[4], "♻️", ":material/recycling:", lambda: None)

    @staticmethod
    def show_actions(folder: str):
        # display_folder = folder.replace(MUSIC_DIR, "")
        with st.expander("🔊 MPD", expanded=True):
            # st.subheader(f"📁 {display_folder}")
            button_container = st.container()
            playlist_container = st.container()
            output_container = st.container()
            with button_container:
                MPD2._add_play_buttons(output_container, folder)
                MPD2.add_playlist_buttons(playlist_container, folder)
                tabs = st.tabs(["Now Playing", "Playlist"])
                with tabs[0]:
                    MPD2._mpd_command("nowplaying", st.container())
                with tabs[1]:
                    MPD2._mpd_command("playlist", st.container())
