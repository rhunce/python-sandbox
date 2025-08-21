import re
import unicodedata
from functools import lru_cache
from typing import List, Tuple, Optional

# ------------------------------
# Normalization & Cleaning
# ------------------------------

def normalize_text(s: str) -> str:
    """
    Unicode compatibility normalization (NFKC).
    Examples:
      'ﬁancé ①' -> 'fiancé 1'
      'ＡＢＣ１２３' -> 'ABC123'
      'x² + y³' -> 'x2 + y3'
    """
    return unicodedata.normalize("NFKC", s)

def clean_text(s: str) -> str:
    """
    Keep only letters/digits/spaces; collapse whitespace; lowercase.
    - Removes punctuation BETWEEN word-chars to *join* fragments (can't->cant, hypoth&&&ses->hypothses).
    - All other punctuation becomes spaces (acts as separators).
    - Preserves accents (é remains).
    """
    s = normalize_text(s)
    s = s.replace("\n", " ")

    # Join inner punctuation: keep word intact when punctuation is between word chars
    s = re.sub(r'(?<=\w)[^\w\s]+(?=\w)', '', s, flags=re.UNICODE)

    # Other punctuation -> spaces
    s = re.sub(r'[^\w\s]+', ' ', s, flags=re.UNICODE)

    # Treat underscores as spaces (since \w includes '_')
    s = s.replace('_', ' ')

    # Collapse spaces and lowercase
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s

# ------------------------------
# Helpers
# ------------------------------

def occurrences(word: str, ch: str) -> List[int]:
    idxs, start = [], 0
    while True:
        i = word.find(ch, start)
        if i == -1:
            return idxs
        idxs.append(i)
        start = i + 1

def choose_anchor_index(word: str, ch: str) -> Optional[int]:
    """Pick occurrence closest to the center (ties -> lower index)."""
    idxs = occurrences(word, ch)
    if not idxs:
        return None
    center = (len(word) - 1) / 2.0
    return min(idxs, key=lambda i: (abs(i - center), i))

def segment_score(anchor_col: int, seg_len: int, min_len: int, max_len: int) -> float:
    """
    Heuristic: anchor near center; penalize too short/long (heavier on long).
    """
    center = (seg_len - 1) / 2.0 if seg_len > 0 else 0.0
    length_penalty = 0.0
    if seg_len < min_len:
        length_penalty += (min_len - seg_len) * 1.0
    if seg_len > max_len:
        length_penalty += (seg_len - max_len) * 2.0
    return abs(anchor_col - center) + length_penalty

# ------------------------------
# Main
# ------------------------------

def arrange_lyrics_chat_gpt(
    lyrics: str,
    band_name: str,
    min_chars: int = 8,
    max_chars: int = 24,
    growth_steps: Optional[List[int]] = None,
) -> str:
    """
    Build a vertical acrostic using a SINGLE CONTIGUOUS slice of the cleaned lyrics.

    Guarantees:
      - No word between the first and last printed word is skipped.
      - First line: anchor word is the FIRST printed word on that line.
      - Last line: anchor word is the LAST printed word on that line.
      - Each line contains the next band-name character (case-insensitive) somewhere in its segment.
      - Returns "CANNOT_ASSEMBLE" if impossible under these constraints.
    """
    if growth_steps is None:
        # Try compact first, relax if needed
        growth_steps = [max_chars, max_chars + 8, max_chars + 16, max_chars + 24, 120]

    text = clean_text(lyrics)
    band = clean_text(band_name).replace(" ", "")
    if not text or not band:
        return "CANNOT_ASSEMBLE"

    words = text.split()
    n, m = len(words), len(band)
    if n == 0 or m == 0:
        return "CANNOT_ASSEMBLE"

    # Prefix sums of word lengths for O(1) segment length (with spaces)
    cumlen = [0] * (n + 1)
    for i in range(n):
        cumlen[i + 1] = cumlen[i] + len(words[i])

    def seg_len(a: int, b: int) -> int:
        return (cumlen[b + 1] - cumlen[a]) + (b - a)

    for max_cap in growth_steps:

        @lru_cache(maxsize=None)
        def candidates(i: int, pos: int):
            """
            Candidate segments for band letter i starting at word index pos.
            Returns tuples:
              (score, a, e, j, anchor_idx_in_word, anchor_col, seg_len_chars)

            Constraints:
              - a == pos always.
              - If i == 0: j MUST equal a (first printed word is first anchor word).
              - If i == m-1: e MUST equal j (last printed word is last anchor word).
              - Always include the 'j-alone' candidate (e == j), even if short/scored worse.
            """
            ch = band[i]
            out = []
            if pos >= n:
                return tuple()

            # Helper to compute one candidate for a given end 'ee'
            def make_candidate(a: int, j: int, ee: int, anchor_in_word: int):
                chars_before_anchor = (cumlen[j] - cumlen[a]) + (j - a)
                anchor_col = chars_before_anchor + anchor_in_word
                L = seg_len(a, ee)
                sc = segment_score(anchor_col, L, min_chars, max_cap)
                return (sc, a, ee, j, anchor_in_word, anchor_col, L)

            TOP_K = 8  # prune branching, but we force-keep 'j-alone'

            j_range = [pos] if i == 0 else range(pos, n)
            for j in j_range:
                if seg_len(pos, j) > max_cap:
                    break
                if ch not in words[j]:
                    if i == 0:
                        break
                    continue
                anchor_in_word = choose_anchor_index(words[j], ch)
                if anchor_in_word is None:
                    if i == 0:
                        break
                    continue

                forced_alone = None  # store 'e == j' candidate to force-keep later

                if i == m - 1:
                    # LAST LINE: must end at the anchor word
                    if seg_len(pos, j) <= max_cap:
                        forced_alone = make_candidate(pos, j, j, anchor_in_word)
                        out.append(forced_alone)
                else:
                    # Non-last lines:
                    # 1) Forced 'j-alone' candidate (may be short)
                    if seg_len(pos, j) <= max_cap:
                        forced_alone = make_candidate(pos, j, j, anchor_in_word)
                        out.append(forced_alone)

                    # 2) Candidates extended to reach >= min_chars (if possible), plus a couple longer
                    e = j
                    while e < n and seg_len(pos, e) < min_chars and seg_len(pos, e) <= max_cap:
                        e += 1
                    e0 = e if e < n and seg_len(pos, e) <= max_cap else max(j, e - 1)

                    tried = set()
                    for off in range(0, 3):
                        ee = e0 + off
                        if ee >= n:
                            break
                        L = seg_len(pos, ee)
                        if L > max_cap:
                            break
                        if (ee, j) in tried:
                            continue
                        tried.add((ee, j))
                        out.append(make_candidate(pos, j, ee, anchor_in_word))

            if not out:
                return tuple()

            # Sort by score, take top-K
            out.sort(key=lambda t: t[0])
            kept = out[:TOP_K]

            # Ensure 'j-alone' candidate(s) are kept (force-keep) for every j we considered
            # (We already included them in 'out'; just ensure not pruned.)
            # Collect forced 'e==j' per unique j
            forced = []
            seen_j = set()
            for cand in out:
                _, a, ee, j, _, _, _ = cand
                if ee == j and (j not in seen_j):
                    forced.append(cand)
                    seen_j.add(j)

            # Merge: keep = top-K ∪ forced_alone (dedup by object identity)
            signature = {(a, e, j, idx, col, L) for _, a, e, j, idx, col, L in kept}
            for cand in forced:
                _, a, ee, j, idx, col, L = cand
                key = (a, ee, j, idx, col, L)
                if key not in signature:
                    kept.append(cand)
                    signature.add(key)

            # Final sort (stable by score)
            kept.sort(key=lambda t: t[0])
            return tuple(kept)

        @lru_cache(maxsize=None)
        def solve(i: int, pos: int):
            """
            DP over lines i..m-1 starting at word index pos.
            Returns (cost, solution_tuple) where solution_tuple is a sequence of
            (a,e,j,anchor_idx,anchor_col).
            """
            INF = (10**9, ())
            if i == m:
                return (0.0, ())
            best = INF
            cands = candidates(i, pos)
            if not cands:
                return INF
            for (sc, a, e, j, aidx, acol, L) in cands:
                nxt_cost, nxt_sol = solve(i + 1, e + 1)
                if nxt_cost >= 1e9:
                    continue
                total = sc + nxt_cost
                if total < best[0]:
                    best = (total, ((a, e, j, aidx, acol),) + nxt_sol)
            return best

        # Start positions must contain the first band letter
        starts = [p for p in range(n) if band[0] in words[p]]
        if not starts:
            continue

        best_overall = (10**9, None)
        for pos0 in starts:
            cost, sol = solve(0, pos0)
            if cost < best_overall[0]:
                best_overall = (cost, sol)

        if best_overall[1] is None:
            continue

        # Reconstruct & align
        sol = best_overall[1]
        target_col = max(acol for (_, _, _, _, acol) in sol)
        lines = []
        for (a, e, j, aidx, acol) in sol:
            seg_words = words[a : e + 1]
            # Uppercase the anchor *letter* (digits remain digits)
            aw = list(seg_words[j - a])
            if 0 <= aidx < len(aw):
                aw[aidx] = aw[aidx].upper()
            seg_words[j - a] = "".join(aw)
            pad = " " * (target_col - acol)
            lines.append(pad + " ".join(seg_words))
        return "\n".join(lines)

    return "CANNOT_ASSEMBLE"

# ==========================================
# ================ EXAMPLES ================
# ==========================================
lyrics_1 = "...I bomb atomically, socrates, ^^^philosophies and hypoth&&&ses can't define h***ow I be dropping these mockeries..."
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

lyrics_12 = "Прекрасное объяснение. Тема сложная, конечно, но лучше никто объяснить не сможет."
band_name_12 = "Т чл ибж"

print(arrange_lyrics_chat_gpt(lyrics_1, band_name_1))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_2, band_name_2))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_3, band_name_3))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_4, band_name_4))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_5, band_name_5))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_6, band_name_6))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_7, band_name_7))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_8, band_name_8))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_9, band_name_9))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_10, band_name_10))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_11, band_name_11))
print("\n")
print(arrange_lyrics_chat_gpt(lyrics_12, band_name_12))
print("\n")


# ======================================
# ================ TIMER ===============
# ======================================
import timeit

N = 10000
total = timeit.timeit(
    stmt="arrange_lyrics_chat_gpt(lyrics, band_name)",
    setup="""
from __main__ import arrange_lyrics_chat_gpt
lyrics = "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book hersister was reading, but it had no pictures or conversations in it, “and what is the use of a book,” thought Alice “without pictures or conversations?” So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her."
band_name = "alice"
""",
    number=N
)

avg_ms = (total / N) * 1000
print(f"Average execution time: {avg_ms:.9f} ms")