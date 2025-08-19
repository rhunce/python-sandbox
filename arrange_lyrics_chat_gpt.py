import unicodedata as ud

CANNOT_ASSEMBLE = "CANNOT_ASSEMBLE"

def arrange_lyrics_pretty(lyrics: str, band_name: str) -> str:
    if not lyrics or not band_name:
        return CANNOT_ASSEMBLE

    # Clean: NFKC normalize, keep letters/digits; keep spaces in lyrics, drop in band
    lyrics = _clean_unicode(lyrics, remove_spaces=False)
    band   = _clean_unicode(band_name, remove_spaces=True)
    if not band:
        return CANNOT_ASSEMBLE

    words = lyrics.split()
    if len(band) > len(words):
        return CANNOT_ASSEMBLE

    # Build per-letter candidate positions: [(word_index, pos_in_word), ...]
    layers = []
    for ch in band:
        occ = _first_occurrences_per_letter(words, ch)
        if not occ:
            return CANNOT_ASSEMBLE
        layers.append(occ)

    # Choose a visually nice path (minimal window → compact/balanced lines)
    selection = _choose_pretty_path(words, layers)
    if not selection:
        return CANNOT_ASSEMBLE

    # Build lines (segment between picks; last line is just last word)
    lines = []
    for i in range(1, len(selection)):
        (w_start, p_start) = selection[i - 1]
        (w_end,   _)       = selection[i]
        seg = list(words[w_start:w_end])
        seg[0] = _capitalize_at(seg[0], p_start)
        lines.append(" ".join(seg))

    w_last, p_last = selection[-1]
    lines.append(_capitalize_at(words[w_last], p_last))

    # Align chosen letters vertically
    aligned = _align_lines_to_column(lines, [pos for _, pos in selection])
    return "\n".join(aligned)


# ---------- helpers ----------

def _clean_unicode(s: str, remove_spaces: bool) -> str:
    """NFKC normalize, then keep only letters/digits (and spaces if allowed)."""
    s = s.replace("\n", " ")
    s = ud.normalize("NFKC", s)
    kept = []
    for ch in s:
        if ch.isalnum() or (ch.isspace() and not remove_spaces):
            kept.append(ch)
        # else drop
    s = "".join(kept)
    # collapse whitespace if keeping spaces
    s = " ".join(s.split()) if not remove_spaces else s.replace(" ", "")
    return s.casefold()  # Unicode-aware lowercase

def _first_occurrences_per_letter(words, letter):
    out = []
    for wi, w in enumerate(words):
        pos = w.find(letter)
        if pos != -1:
            out.append((wi, pos))
    return out

def _capitalize_at(word: str, pos: int) -> str:
    # Works for Unicode letters; digits remain unchanged.
    return word[:pos] + word[pos].upper() + word[pos+1:]

def _choose_pretty_path(words, layers):
    """
    Primary: minimal window (last_wi - first_wi).
    Then:    minimal max line width,
             minimal imbalance |max_left - max_right|,
             minimal total width.
    """
    # prefix sums for fast segment width: len(' '.join(words[i:j]))
    n = len(words)
    pref = [0]*(n+1)
    for i, w in enumerate(words, 1):
        pref[i] = pref[i-1] + len(w)

    def seg_len(i, j):
        if j <= i: return 0
        return (pref[j] - pref[i]) + (j - i - 1)

    # DP across layers; keep best record per candidate in each next layer
    prev = []
    for wi, pos in layers[0]:
        prev.append(((0,0,0,0), wi, 0,0, 0,0, [(wi, pos)]))  # (score,start,maxL,maxR,maxW,sumW,path)

    for li in range(1, len(layers)):
        curr = layers[li]
        best_for_idx = [None]*len(curr)
        for (score, start, mL, mR, mW, sW, path) in prev:
            pwi, ppos = path[-1]
            # advance to any later candidate
            for j, (wi, pos) in enumerate(curr):
                if wi <= pwi: continue
                width = seg_len(pwi, wi)
                left  = ppos
                right = (width - 1) - ppos
                nmL = max(mL, left)
                nmR = max(mR, right)
                nmW = max(mW, width)
                nsW = sW + width
                span = wi - start
                score_key = (span, nmW, abs(nmL - nmR), nsW)
                rec = (score_key, start, nmL, nmR, nmW, nsW, path + [(wi, pos)])
                if best_for_idx[j] is None or rec[0] < best_for_idx[j][0]:
                    best_for_idx[j] = rec
        prev = [r for r in best_for_idx if r is not None]
        if not prev:
            return None

    # finalize: account for the last (single-word) line
    best = None
    for (score_key, start, mL, mR, mW, sW, path) in prev:
        last_wi, last_pos = path[-1]
        lw = len(words[last_wi])
        ll = last_pos
        lr = lw - 1 - last_pos
        fW = max(mW, lw)
        fL = max(mL, ll)
        fR = max(mR, lr)
        fS = sW + lw
        span = last_wi - start
        final_key = (span, fW, abs(fL - fR), fS)
        cand = (final_key, path)
        if best is None or cand[0] < best[0]:
            best = cand
    return best[1] if best else None

def _align_lines_to_column(lines, positions):
    left = max(positions)
    right = max((len(line) - 1 - pos) for line, pos in zip(lines, positions))
    total = left + 1 + right
    out = []
    for line, pos in zip(lines, positions):
        lp = left - pos
        rp = total - lp - len(line)
        out.append((" " * lp) + line + (" " * rp))
    return out



# ==========================================
# ================ EXAMPLES ================
# ==========================================
lyrics_1 = "...I bomb atomically, socrates, philosophies and hypotheses can't define how I be dropping these mockeries..."
band_name_1 = "cebi"

lyrics_2 = """
Alice was beginning to get very tired of sitting by her sister on the bank,
and of having nothing to do: once or twice she had peeped into the book her
sister was reading, but it had no pictures or conversations in it, “and what
is the use of a book,” thought Alice “without pictures or conversations?”

So she was considering in her own mind (as well as she could, for the hot day
made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain
would be worth the trouble of getting up and picking the daisies, when suddenly a
White Rabbit with pink eyes ran close by her.
"""
band_name_2 = "alice"

lyrics_3 = "a a a a a b b b b b c c c c c"
band_name_3 = "abc"

lyrics_4 = "aaaaa bbbbb x ccccc a bb c"
band_name_4 = "abc"

# Returns "CANNOT_ASSEMBLE" if band name longer than lyrics
lyrics_5 = "aaa"
band_name_5 = "aaaa"

# Returns "CANNOT_ASSEMBLE" if band name not in lyrics
lyrics_6 = "aaa bbb"
band_name_6 = "aba"

# Returns "CANNOT_ASSEMBLE" if band name empty
lyrics_7 = ""
band_name_7 = "aba"

# Returns "CANNOT_ASSEMBLE" if lyrics empty
lyrics_8 = ""
band_name_8 = "aba"

lyrics_9 = "zócalo ola kíndër ejemplo mañana tvityv tótem hjboyu internet niño gélido"
band_name_9 = "Zoë Eñótié"

lyrics_10 = "zócalo          ola kíndër ejemplo mañana          tvityv tótem hjboyu internet niño gélido"
band_name_10 = "Zoë       Eñótié"

lyrics_11 = "ﬁancé ① ＡＢＣ１２３ x² + y³"
band_name_11 = "i1bx3"

print(arrange_lyrics_pretty(lyrics_1, band_name_1))
print("\n")
print(arrange_lyrics_pretty(lyrics_2, band_name_2))
print("\n")
print(arrange_lyrics_pretty(lyrics_3, band_name_3))
print("\n")
print(arrange_lyrics_pretty(lyrics_4, band_name_4))
print("\n")
print(arrange_lyrics_pretty(lyrics_5, band_name_5))
print("\n")
print(arrange_lyrics_pretty(lyrics_6, band_name_6))
print("\n")
print(arrange_lyrics_pretty(lyrics_7, band_name_7))
print("\n")
print(arrange_lyrics_pretty(lyrics_8, band_name_8))
print("\n")
print(arrange_lyrics_pretty(lyrics_9, band_name_9))
print("\n")
print(arrange_lyrics_pretty(lyrics_10, band_name_10))
print("\n")
print(arrange_lyrics_pretty(lyrics_11, band_name_11))
print("\n")


# ======================================
# ================ TIMER ===============
# ======================================
import timeit

N = 10000
total = timeit.timeit(
    stmt="arrange_lyrics_pretty(lyrics, band_name)",
    setup="""
from __main__ import arrange_lyrics_pretty
lyrics = "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book hersister was reading, but it had no pictures or conversations in it, “and what is the use of a book,” thought Alice “without pictures or conversations?” So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her."
band_name = "alice"
""",
    number=N
)

avg_ms = (total / N) * 1000
print(f"Average execution time: {avg_ms:.9f} ms")