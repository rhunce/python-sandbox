import re
from bisect import bisect_right


def first_occurrences_per_letter(words, letter):
    """Return [(word_index, pos_in_word)] for the FIRST occurrence in each word."""
    out = []
    for wi, w in enumerate(words):
        pos = w.find(letter)
        if pos != -1:
            out.append((wi, pos))
    return out

def min_range_strictly_increasing(lists):
    """
    lists: [ [(wi, pos), ...], [(wi, pos), ...], ... ]
    Pick one (wi, pos) from each inner list so that wi is strictly increasing
    across layers, and the span (last_wi - first_wi) is minimized.
    Returns the best list of tuples, or None if impossible.
    """
    if not lists or any(not lst for lst in lists):
        return None

    # Ensure each layer is sorted by word index and precompute keys for bisect
    arrays = [sorted(lst, key=lambda t: t[0]) for lst in lists]
    keys   = [[wi for wi, _ in arr] for arr in arrays]

    best = None

    # Try each start candidate from the first layer
    for start_wi, start_pos in arrays[0]:
        sel = [(start_wi, start_pos)]
        prev_wi = start_wi
        feasible = True

        # For each subsequent layer, pick the first occurrence with wi > prev_wi
        for arr, ks in zip(arrays[1:], keys[1:]):
            i = bisect_right(ks, prev_wi)
            if i == len(arr):
                feasible = False
                break
            wi, pos = arr[i]
            sel.append((wi, pos))
            prev_wi = wi

        if feasible:
            if best is None:
                best = sel
            else:
                cand_span = sel[-1][0] - sel[0][0]
                curr_span = best[-1][0] - best[0][0]
                if cand_span < curr_span or (cand_span == curr_span and sel < best):
                    best = sel

    return best

# O(l) time | O(l) space
def arrange_lyrics_improved(lyrics, band_name):
  # Guard: empty band name
  if not lyrics or not band_name:
    return ""
  
  # 1) Clean + lowercase
  # split on \n and join on " "
  lyrics = " ".join(lyrics.split("\n"))
  lyrics = re.sub(r'[^a-zA-Z0-9 ]', '', lyrics).lower()
  
  band_name = band_name.lower()

  # 2) Split to words
  words = lyrics.split()

  layers = []
  for ch in band_name:
      occ = first_occurrences_per_letter(words, ch)
      if not occ:
          return ""  # impossible
      layers.append(occ)

  best_selection = min_range_strictly_increasing(layers)

  print("*** best_selection: ", best_selection)

  # Guard: band name longer than lyrics
  if len(band_name) > len(words):
    return ""

  # 4) Construct lines
  lines = []
  for i in range(1, len(best_selection)):
    start_index, _ = best_selection[i-1]
    end_index, _ = best_selection[i]
    line = " ".join(words[start_index:end_index])
    lines.append(line)
  lines.append(words[best_selection[-1][0]])

  print("*** lines: ", lines)

  # 5) Determine padding to align vertically
  left_buffer = 0
  right_buffer = 0
  for i, line in enumerate(lines):
    left_buffer = max(left_buffer, best_selection[i][1])
    right_buffer = max(right_buffer, len(line) - 1 - best_selection[i][1])

  # 6) Add the buffers to the lines
  for i, line in enumerate(lines):
    needed_left_buffer = left_buffer - best_selection[i][1]
    needed_right_buffer = right_buffer - (len(line) - 1 - best_selection[i][1])
    if not needed_left_buffer and not needed_right_buffer:
      continue
    line_left_buffer = " " * needed_left_buffer
    line_right_buffer = " " * needed_right_buffer
    lines[i] = line_left_buffer + line + line_right_buffer
  
  return "\n".join(lines)




# EXAMPLES
lyrics = "...I bomb atomically, socrates, philosophies and hypotheses can't define how I be dropping these mockeries..."
band_name = "cebi"
print(arrange_lyrics_improved(lyrics, band_name))

print("\n")

lyrics = "Sometimes under the sun"
band_name = "tus"
print(arrange_lyrics_improved(lyrics, band_name))

print("\n")

lyrics = """
Alice was beginning to get very tired of sitting by her sister on the bank,
and of having nothing to do: once or twice she had peeped into the book her
sister was reading, but it had no pictures or conversations in it, “and what
is the use of a book,” thought Alice “without pictures or conversations?”

So she was considering in her own mind (as well as she could, for the hot day
made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain
would be worth the trouble of getting up and picking the daisies, when suddenly a
White Rabbit with pink eyes ran close by her.
"""

band_name = "alice"
print(arrange_lyrics_improved(lyrics, band_name))

print("\n")

lyrics = ".....zzzzz Aaaaaaaaaaaaaaaaaaaaaaaaaaaaa xxxxxxxxxxxx Bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb xxxxxxxxxxxx Ccccccccccccccccccccccccccccccccccccccccc xxxxxxxxxxxx Ddddddddddddddddddddddddddddddddddddddddddddddddddddddddd zzzzzz......"

band_name = "abcd"
print(arrange_lyrics_improved(lyrics, band_name))


# TIMER
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

# FOLLOW UP QUESTIONS
# ----------  1. How do we handle the case where the band name is not in the lyrics?
# 2. How can we improve this algorithm? What is the time and space complexity?
# 3. Is there a better algorithm? What is the time and space complexity?
# 4. What tests would you write for this function?
# 5. What if there are multiple arrangements? How should we best deal with this?
# 6. How would we capitalize the band name in the output?
# 7. Time this function.
# 8. This is left-side biased. How can we make it right-side biased?
# 9 . ...