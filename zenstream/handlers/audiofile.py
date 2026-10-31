from mutagen.easyid3 import EasyID3


class AudioFile:
    """Class for extracting metadata from audio files"""

    @staticmethod
    def get_id3_tag(file_path: str) -> dict:
        """Extract ID3 tags from an audio file."""
        try:
            audio = EasyID3(file_path)
            return {key.title(): value[0] for key, value in audio.items()}
        except Exception:
            return {}
