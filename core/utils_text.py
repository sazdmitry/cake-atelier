import re
import unicodedata

def normalize_text(s: str) -> str:
    if s is None:
        return ''
    # Lowercase, strip, NFKD normalize, remove diacritics, collapse spaces
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii')
    s = s.lower().strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def stable_hash(parts: list[str]) -> str:
    import hashlib
    joined = '|'.join(parts)
    return hashlib.sha1(joined.encode('utf-8')).hexdigest()
