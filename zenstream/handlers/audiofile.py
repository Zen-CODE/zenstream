from mutagen.easyid3 import EasyID3
from mutagen import File
from os import sep


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

    @staticmethod
    def get_mp3_meta(file_path: str) -> dict:
        """Extract metadata from an MP3 file."""
        info: File = File(file_path).info
        parts = file_path.split(sep)
        return {
            "Artist": parts[-3],
            "Album": parts[-2],
            "Track": parts[-1],
            "Length": f"{int(info.length // 60)}m {int(info.length % 60)}s",
            "Bitrate": f"{info.bitrate // 1000}kbps",
            "Bitrate mode": AudioFile._get_bitrate(info),
            "Channels": info.channels,
            "Sample rate": f"{info.sample_rate}hz",
        }

    @staticmethod
    def _get_bitrate(info_obj: File) -> str:
        """
        Return the bitrate description given the mutagen bitrate object.
        """
        bitrate_mode = getattr(info_obj, "bitrate_mode", None)
        if bitrate_mode is None:
            return "unknown"
        val = int(bitrate_mode)
        return ["Unknown", "CBR", "VBR", "ABR"][val]
