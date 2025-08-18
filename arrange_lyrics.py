import re

# O(l) time | O(l) space
def arrange_lyrics(lyrics, band_name):
  # Guard: empty band name
  if not lyrics or not band_name:
    return ""
  
  # 1) Clean + lowercase inputs
  # split on \n and join on " "
  lyrics = " ".join(lyrics.split("\n"))
  lyrics = re.sub(r'[^a-zA-Z0-9 ]', '', lyrics).lower()
  
  band_name = band_name.lower()

  # 2) Split to words
  words = lyrics.split()

  # Guard: band name longer than lyrics
  if len(band_name) > len(words):
    return ""

  # 3) Greedily pick, in order, the earliest word that contains each needed letter.
  #    Record: index of that word, and the index of the letter within that word.
  word_idxs = []
  letter_in_word_idxs = []
  letter_index = 0
  len_band_name = len(band_name)
  for i, word in enumerate(words):
    if letter_index == len_band_name:
      break
    j = word.find(band_name[letter_index])
    if j != -1:
      word_idxs.append(i)
      letter_in_word_idxs.append(j)
      # Capitalize the letter in the word
      words[i] = word[:j] + word[j].upper() + word[j+1:]
      letter_index += 1

  # Guard: band name not fully in lyrics
  if letter_index != len_band_name:
    return ""

  # 4) Construct lines
  lines = []
  for i in range(1, len(word_idxs)):
    start_index = word_idxs[i-1]
    end_index = word_idxs[i]
    line = " ".join(words[start_index:end_index])
    lines.append(line)
  lines.append(words[word_idxs[-1]])

  # 5) Determine padding to align vertically
  left_buffer = 0
  right_buffer = 0
  for i, line in enumerate(lines):
    left_buffer = max(left_buffer, letter_in_word_idxs[i])
    right_buffer = max(right_buffer, len(line) - 1 - letter_in_word_idxs[i])

  # 6) Add the buffers to the lines
  for i, line in enumerate(lines):
    needed_left_buffer = left_buffer - letter_in_word_idxs[i]
    needed_right_buffer = right_buffer - (len(line) - 1 - letter_in_word_idxs[i])
    if not needed_left_buffer and not needed_right_buffer:
      continue
    line_left_buffer = " " * needed_left_buffer
    line_right_buffer = " " * needed_right_buffer
    lines[i] = line_left_buffer + line + line_right_buffer
  
  return "\n".join(lines)


# ==========================================
# ================ EXAMPLES ================
# ==========================================
lyrics_1 = "...I bomb atomically, socrates, philosophies and hypotheses can't define how I be dropping these mockeries..."
band_name_1 = "cebi"

lyrics_2 = "Sometimes under the sun"
band_name_2 = "tus"

lyrics_3 = """
Alice was beginning to get very tired of sitting by her sister on the bank,
and of having nothing to do: once or twice she had peeped into the book her
sister was reading, but it had no pictures or conversations in it, “and what
is the use of a book,” thought Alice “without pictures or conversations?”

So she was considering in her own mind (as well as she could, for the hot day
made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain
would be worth the trouble of getting up and picking the daisies, when suddenly a
White Rabbit with pink eyes ran close by her.
"""
band_name_3 = "alice"

print(arrange_lyrics(lyrics_1, band_name_1))
print("\n")
print(arrange_lyrics(lyrics_2, band_name_2))
print("\n")
print(arrange_lyrics(lyrics_3, band_name_3))
print("\n")

# ======================================
# ================ TIMER ===============
# ======================================
import timeit

N = 10000
total = timeit.timeit(
    stmt="arrange_lyrics(lyrics, band_name)",
    setup="""
from __main__ import arrange_lyrics
lyrics = \"\"\"Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or 
twice she had peeped into the book hersister was reading, but it had no pictures or conversations in it, 
“and what is the use of a book,” thought Alice “without pictures or conversations?” So she was considering 
in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure
 of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit 
 with pink eyes ran close by her.\"\"\"
band_name = "alice"
""",
    number=N
)

avg_ms = (total / N) * 1000
print(f"Average execution time: {avg_ms:.9f} ms")