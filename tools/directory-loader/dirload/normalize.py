"""Small, dependency free cleaners used by every source and by the deduper."""
import re
import unicodedata

_STOP = {"the", "inc", "llc", "ltd", "co", "corp", "company", "and", "of"}


def phone(raw, default_cc="1"):
    """Return E.164 (+15551234567) or None. Assumes North America when 10 digits."""
    if not raw:
        return None
    raw = str(raw).split(";")[0]
    digits = re.sub(r"\D", "", raw)
    if raw.strip().startswith("+") and 8 <= len(digits) <= 15:
        return "+" + digits
    if len(digits) == 10:
        return "+" + default_cc + digits
    if len(digits) == 11 and digits.startswith(default_cc):
        return "+" + digits
    return None


def website(raw):
    if not raw:
        return None
    url = str(raw).split(";")[0].strip()
    if not url:
        return None
    if not re.match(r"^https?://", url, re.I):
        url = "http://" + url
    return url


def host(url):
    if not url:
        return None
    m = re.match(r"^https?://(?:www\.)?([^/:?#]+)", url, re.I)
    return m.group(1).lower() if m else None


def name_key(name):
    """Lowercase ASCII tokens without punctuation and filler words, for matching."""
    if not name:
        return ""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " and ").replace("'", "")
    toks = [t for t in re.split(r"[^a-z0-9]+", s) if t and t not in _STOP]
    return " ".join(toks)


def name_similar(a, b):
    """Token Jaccard similarity of two name keys, 0..1.

    When every token of the shorter name (at least 2 tokens) appears in the longer
    one, the score is at least 0.85 ("joes pizza" vs "joes pizza bar"). A single
    word such as "northwestern" never counts as containment, so big campuses
    with many offices do not chain together.
    """
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    jac = len(ta & tb) / len(ta | tb)
    small, big = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(small) >= 2 and small <= big:
        return max(jac, 0.85)
    return jac
