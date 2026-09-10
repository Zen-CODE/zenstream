def get_ext(file_name: str) -> str:
    """Return the lowercase file extension (without leading dot)."""
    return file_name.split(".")[-1].lower()
