import re
import unicodedata

CANNOT_ASSEMBLE = "CANNOT_ASSEMBLE"

# O(...?...) time | O(...?...)
def arrange_lyrics_improved(lyrics, band_name):
  # Guard: empty band name
  if not lyrics or not band_name:
    return CANNOT_ASSEMBLE
  
  # 1) Clean + lowercase inputs
  lyrics = clean_text(lyrics)
  band_name = clean_text(band_name, True)

  # 2) Split lyrics into words
  words = lyrics.split()

  # Guard: band name longer than available words
  if len(band_name) > len(words):
    return CANNOT_ASSEMBLE

  # 3) For each letter in band_name, make a list of tuples of the index of words 
  #    where it occurs, and the first index of the letter within that word.
  layers = []
  for ch in band_name:
      occurrences = get_first_occurrences_of_letter_in_words(words, ch)
      if not occurrences:
          return CANNOT_ASSEMBLE
      layers.append(occurrences)

  # 4) Find the smallest range of words that contains all the letters in band_name.
  best_selection = get_min_range_of_words_having_letters(layers)

  # Guard: no solution
  if not best_selection:
    return CANNOT_ASSEMBLE

  # 5) Construct lines
  lines = []
  for i in range(1, len(best_selection)):
    start_index, pos_of_letter_in_word = best_selection[i-1]
    end_index, _ = best_selection[i]
    # Capitalize the letter in the word
    words[start_index] = capitalize_letter_in_word(words[start_index], pos_of_letter_in_word)
    line = " ".join(words[start_index:end_index])
    lines.append(line)
  # Construct and append last line
  last_word_index, pos = best_selection[-1]
  words[last_word_index] = capitalize_letter_in_word(words[last_word_index], pos)
  lines.append(words[last_word_index])

  # 6) Determine padding to align vertically
  left_buffer = 0
  right_buffer = 0
  for i, line in enumerate(lines):
    left_buffer = max(left_buffer, best_selection[i][1])
    right_buffer = max(right_buffer, len(line) - 1 - best_selection[i][1])

  # 7) Add the buffers to the lines
  for i, line in enumerate(lines):
    needed_left_buffer = left_buffer - best_selection[i][1]
    needed_right_buffer = right_buffer - (len(line) - 1 - best_selection[i][1])
    if not needed_left_buffer and not needed_right_buffer:
      continue
    line_left_buffer = " " * needed_left_buffer
    line_right_buffer = " " * needed_right_buffer
    lines[i] = line_left_buffer + line + line_right_buffer
  
  return "\n".join(lines)


# =========================================
# ================ HELPERS ================
# =========================================
def clean_text(s: str, remove_spaces: bool = False) -> str:
    """
    Normalize, then keep only alphanumeric characters from any language.
    If remove_spaces=True, drop spaces (e.g. for band_name); else keep spaces (e.g. for lyrics).
    E.g. s = ...abc^@#$%^123... → s = abc123
    """
    s = s.replace("\n", " ")
    # The following line of code, with the "NFKC" argument, makes “quirky” characters become their plain forms first, so they don’t get dropped
    # Examples:
    # ﬁancé ① → fiancé 1
    # ＡＢＣ１２３ → ABC123
    # x² + y³ → x2 + y3
    s = unicodedata.normalize("NFKC", s)
    if remove_spaces:
        s = "".join(ch for ch in s if ch.isalnum())
    else:
        s = "".join(ch for ch in s if (ch.isalnum() or ch.isspace()))
    return s.lower()

def get_first_occurrences_of_letter_in_words(words, letter):
    """Return [(word_index, pos_in_word)] for the FIRST occurrence in each word."""
    out = []
    for wi, w in enumerate(words):
        pos = w.find(letter)
        if pos != -1:
            out.append((wi, pos))
    return out

def get_min_range_of_words_having_letters(lists):
    """
    lists: [ [(wi, pos), ...], ... ]
    Objective: minimize (last_wi - first_wi).
    Tie: keep the first encountered minimum (by iteration order).
    """
    if not lists or any(not lst for lst in lists):
        return None

    best = None
    best_span = float('inf')

    for start_wi, start_pos in lists[0]:
        sel = [(start_wi, start_pos)]
        prev_wi = start_wi
        feasible = True

        # For each subsequent layer, linearly find the first wi > prev_wi
        for arr in lists[1:]:
            j = 0
            while j < len(arr) and arr[j][0] <= prev_wi:
                j += 1
            if j == len(arr):
                feasible = False
                break
            wi, pos = arr[j]
            sel.append((wi, pos))
            prev_wi = wi

        if not feasible:
            continue

        span = sel[-1][0] - sel[0][0]
        if span < best_span:
            best = sel
            best_span = span

    return best

def capitalize_letter_in_word(word, pos):
    return word[:pos] + word[pos].upper() + word[pos+1:]


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

print(arrange_lyrics_improved(lyrics_1, band_name_1))
print("\n")
print(arrange_lyrics_improved(lyrics_2, band_name_2))
print("\n")
print(arrange_lyrics_improved(lyrics_3, band_name_3))
print("\n")
print(arrange_lyrics_improved(lyrics_4, band_name_4))
print("\n")
print(arrange_lyrics_improved(lyrics_5, band_name_5))
print("\n")
print(arrange_lyrics_improved(lyrics_6, band_name_6))
print("\n")
print(arrange_lyrics_improved(lyrics_7, band_name_7))
print("\n")
print(arrange_lyrics_improved(lyrics_8, band_name_8))
print("\n")
print(arrange_lyrics_improved(lyrics_9, band_name_9))
print("\n")
print(arrange_lyrics_improved(lyrics_10, band_name_10))
print("\n")
print(arrange_lyrics_improved(lyrics_11, band_name_11))
print("\n")


# ======================================
# ================ TIMER ===============
# ======================================
# import timeit

# N = 10000
# total = timeit.timeit(
#     stmt="arrange_lyrics_improved(lyrics, band_name)",
#     setup="""
# from __main__ import arrange_lyrics_improved
# lyrics = "Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book hersister was reading, but it had no pictures or conversations in it, “and what is the use of a book,” thought Alice “without pictures or conversations?” So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her."
# band_name = "alice"
# """,
#     number=N
# )

# avg_ms = (total / N) * 1000
# print(f"Average execution time: {avg_ms:.9f} ms")