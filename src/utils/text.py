import textwrap


def wrap_lines(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def ffmpeg_escape(s: str) -> str:
    """
    FFmpeg drawtext escaping.
    We keep it conservative to avoid "Invalid argument" issues.
    """
    s = s.replace("\\", "\\\\")
    s = s.replace(":", "\\:")
    s = s.replace("'", "\\'")
    s = s.replace(",", "\\,")
    s = s.replace("[", "\\[")
    s = s.replace("]", "\\]")
    s = s.replace("\n", "\\n")
    return s
