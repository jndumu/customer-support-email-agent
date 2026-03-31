"""Text preprocessing helpers for email bodies."""

import re
import unicodedata


# Common email signature delimiters
_SIGNATURE_PATTERNS = [
    r"--\s*\n",
    r"_{3,}",
    r"Sent from my (iPhone|Android|Galaxy|Outlook|Mail)",
    r"Get Outlook for",
    r"From:\s.+@.+",
    r"On .+ wrote:",
    r"-----Original Message-----",
]
_SIGNATURE_RE = re.compile(
    "|".join(_SIGNATURE_PATTERNS), re.IGNORECASE | re.MULTILINE
)


def clean_email_body(raw: str) -> str:
    """Strip signatures, quoted replies, excessive whitespace."""
    # Remove quoted reply blocks (lines starting with >)
    lines = raw.splitlines()
    clean_lines = [l for l in lines if not l.strip().startswith(">")]
    text = "\n".join(clean_lines)

    # Cut at first signature delimiter
    match = _SIGNATURE_RE.search(text)
    if match:
        text = text[: match.start()]

    # Normalise unicode
    text = unicodedata.normalize("NFKC", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_sender_name(sender: str) -> str:
    """Extract display name from 'Name <email@domain>' format."""
    match = re.match(r"^(.+?)\s*<.+>$", sender.strip())
    if match:
        return match.group(1).strip().strip('"')
    # fall back to the part before @
    local = sender.split("@")[0]
    return local.replace(".", " ").replace("_", " ").title()


def truncate_text(text: str, max_chars: int = 3000) -> str:
    """Hard-truncate text to avoid exceeding token limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[... truncated ...]"


def build_raw_email(sender: str, subject: str, body: str) -> str:
    return f"From: {sender}\nSubject: {subject}\n\n{body}"
