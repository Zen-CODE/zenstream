from glob import glob
from os import sep

import streamlit as st

from styler import Styler
from utils import get_ext
from handlers.audiofile import AudioFile


class AudioPlayer:
    @staticmethod
    def _show_meta(file_name: str):
        data = AudioFile.get_mp3_meta(file_name)
        Styler.show_dict("Track Metadata", data)

        if get_ext(file_name) == "mp3":
            data = AudioFile.get_id3_tag(file_name)
            if data:
                Styler.show_dict("ID3 Tag", data)
            else:
                st.warning(f"No ID3 data for {file_name}")

    @staticmethod
    def show_file(file_name: str):
        """Display the audio player, metadata and cover image."""

        st.header("Audio Player")
        st.audio(file_name, autoplay=True)

        if get_ext(file_name) == "mp3":
            st.markdown("**Metadata**")
            AudioPlayer._show_meta(file_name)
            AudioPlayer._show_cover(file_name)

    @staticmethod
    def _show_cover(file_name: str):
        def get_cover() -> str:
            parts = file_name.split(sep)
            folder = sep.join(parts[:-1])
            for image in glob(sep.join([folder, "cover.*"])):
                return image

        image_path = get_cover()
        if image_path:
            st.markdown("**Album Cover**")
            st.image(image_path)
