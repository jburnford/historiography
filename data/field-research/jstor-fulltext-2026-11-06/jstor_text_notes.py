"""Cut foot- and endnotes out of JSTOR page text, for items JSTOR delivered without a note list (2026-11-06).

Page strings are flat (no line breaks). A note starts with its number before a capital, quote or bracket
('12 Author, Title', '(12) Ibid.', '12. See'). Each number usually appears twice: as the reference in the body and
as the note start below it (footnotes at the page foot, endnotes at the end of the article). The note start is the
later one, so the chain is built backwards: from the highest number N take its last occurrence, then the last
occurrence of N-1 before it, and so on down to 1, allowing a few gaps (numbers OCR lost). A note runs to the next
note start or to the end of its page (the next page's body text sits between two footnotes).

notes(pages) -> list of note strings in order, or [] when no convincing chain is found. The strings feed
jstor_notes.citations() exactly like JSTOR's own lists.
"""
import re

MARK = re.compile(r'(?:(?<=\s)|(?<=^))[(\[]?(\d{1,3})[)\].]?\s+(?=[A-ZÀ-Ý“"‘\'«(\[¿¡]|(?:see|cf|ibid|for|on|in|vgl|voir)\b)', re.I)
CITE = re.compile(r'(?:1[5-9]|20)\d\d|\bibid\b|\bop\.\s?cit|\bpp?\.\s?\d|\bS\.\s?\d', re.I)


def candidates(pages):
    out = []   # (value, page, start, end)
    for pi, page in enumerate(pages):
        for m in MARK.finditer(page):
            v = int(m.group(1))
            if 1 <= v <= 400:
                out.append((v, pi, m.start(), m.end()))
    return out


def chain_from(cands, top, max_gap=3):
    """Backwards greedy chain from the last occurrence of `top`."""
    by_val = {}
    for c in cands:
        by_val.setdefault(c[0], []).append(c)
    if top not in by_val:
        return []
    chain = [by_val[top][-1]]
    v, gaps = top - 1, 0
    while v >= 1:
        pos = (chain[-1][1], chain[-1][2])
        prev = [c for c in by_val.get(v, []) if (c[1], c[2]) < pos]
        if prev:
            chain.append(prev[-1])
        else:
            gaps += 1
            if gaps > max_gap:
                return []
        v -= 1
    return chain[::-1]


def notes(pages, min_notes=5):
    pages = [p if isinstance(p, str) else '' for p in pages]
    cands = candidates(pages)
    if not cands:
        return []
    best = []
    for top in sorted({c[0] for c in cands}, reverse=True):   # the highest number that chains down to 1 is the last note
        if top < min_notes:
            break
        ch = chain_from(cands, top, max_gap=max(3, top // 7))
        if len(ch) >= min_notes and len(ch) > len(best):
            best = ch
            break
    if not best:
        return []
    out = []
    for k, (v, pi, s, e) in enumerate(best):
        if k + 1 < len(best) and best[k + 1][1] == pi:
            text = pages[pi][e:best[k + 1][2]]
        else:
            text = pages[pi][e:]
        out.append(text.strip())
    # a chain of numbered paragraphs or a table is not notes: most notes must look like citations
    citey = sum(1 for t in out if CITE.search(t[:400]))
    if citey < 0.4 * len(out):
        return []
    # the last note on a page can swallow body text of a later page cut (endnotes) or a running head: cap length
    return [t[:2500] for t in out]
