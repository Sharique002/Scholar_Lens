import re
import unicodedata

HTML_TAG_RE = re.compile(r'<[^>]+>')
PUNCT_RE = re.compile(r'[^\w\s]')
WHITESPACE_RE = re.compile(r'\s+')


def normalise_title(s: str) -> str:
    """Normalise paper title for deduplication and fuzzy matching.

    1. Strip HTML tags
    2. Convert '&' to 'and'
    3. NFKD unicode decomposition and strip accents
    4. Replace punctuation with spaces
    5. Convert to lowercase
    6. Collapse whitespace and strip
    """
    if not s:
        return ''
    # Strip HTML
    text = HTML_TAG_RE.sub(' ', s)
    # Replace & with and
    text = text.replace('&', ' and ')
    # NFKD and strip combining accents
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Replace punctuation with spaces
    text = PUNCT_RE.sub(' ', text)
    # Lowercase
    text = text.lower()
    # Collapse whitespace
    text = WHITESPACE_RE.sub(' ', text).strip()
    return text
