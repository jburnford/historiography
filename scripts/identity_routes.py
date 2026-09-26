"""Deterministic helpers for the registry's identity routes (IDENTITY-PLAN.md steps 2.3-2.4).

Name compatibility is only a gate *within* a context that already ties a credit to a person:
the same ISBN, the same reviewed title, the same review URL, or the same catalogued work.
It never matches people on its own, and it cannot separate homonyms.
"""
import re
import unicodedata

DROP = {"jr", "sr", "ii", "iii", "iv", "ed", "eds", "hrsg", "hg", "dr", "prof", "professor", "sir", "rev"}
TITLE_STOP = {"the", "a", "an", "der", "die", "das", "le", "la", "les", "el", "los", "il"}


def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("ß", "ss").replace("ø", "o").replace("æ", "ae").replace("ł", "l").lower()


def tokens(s):
    return [t for t in re.split(r"[^a-z]+", fold(s)) if t and t not in DROP]


def compatible(credit, given, family):
    """Credit name vs one (given, family) variant: family tokens at either end, first initials agree."""
    c, f, g = tokens(credit), tokens(family), tokens(given)
    if not c or not f or not g or len(c) <= len(f):
        return False
    if c[-len(f):] == f:
        rest = c[:-len(f)]
    elif c[:len(f)] == f:          # family-first order, or "Surname, Given"
        rest = c[len(f):]
    else:
        return False
    return rest[0][0] == g[0][0]


def end_tokens(name):
    """First and last name tokens, space-joined: a blocking key covering both name orders."""
    t = tokens(name)
    return " ".join(sorted({t[0], t[-1]})) if t else None


def split_full(name):
    t = (name or "").strip()
    if "," in t:
        family, given = t.split(",", 1)
        return given.strip(), family.strip()
    parts = t.split()
    return (" ".join(parts[:-1]), parts[-1]) if len(parts) > 1 else ("", t)


def variants(given, family, credit=None, others=()):
    out = []
    if family:
        out.append((given or "", family))
    for full in [credit, *others]:
        if full:
            out.append(split_full(full))
    return out


def compatible_any(credit, variant_list):
    return any(compatible(credit, g, f) for g, f in variant_list)


def isbn13(value):
    v = re.sub(r"[^0-9Xx]", "", value or "").upper()
    if len(v) == 13 and v.isdigit():
        return v if sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(v)) % 10 == 0 else None
    if len(v) == 10:
        body = "978" + v[:9]
        if not body.isdigit():
            return None
        if sum((10 - i) * (10 if ch == "X" else int(ch)) for i, ch in enumerate(v)) % 11 != 0:
            return None
        check = (10 - sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(body)) % 10) % 10
        return body + str(check)
    return None


def title_key(title):
    """Main title (before subtitle punctuation), folded, leading article dropped.
    Returns None when too short to identify a book on its own."""
    main = re.split(r"\s*[:;.?!]\s|\s+[-–—]\s+|\s*[:;]\s*", title or "", maxsplit=1)[0]
    t = tokens(main)
    if t and t[0] in TITLE_STOP:
        t = t[1:]
    key = " ".join(t)
    return key if len(t) >= 3 or len(key) >= 18 else None


def folded_text(s):
    return " ".join(re.split(r"[^a-z0-9]+", fold(s))).strip()
