"""

Inputs:
- lyrics: string
- band_name: string

Output:
- The lyrics arranged in such a way that the band name is spelled vertically therein: string
- Remove all non-alphanumeric characters

Example:
lyrics = "...I bomb atomically, socrates, philosophies and hypotheses can't define how I be dropping these mockeries..."
band_name = "miee"

output =  "       atomiCally, 
                 socratEs philosophies and hypotheses cant define how I 
                       Be 
                  droppIng"
                       ^
"""
import re

def arrange_lyrics_improved(lyrics, band_name):
  # Remove all non-alphanumeric characters and make lowercase
  lyrics = re.sub(r'[^a-zA-Z0-9 ]', '', lyrics).lower()
  band_name = band_name.lower()

  # Split the lyrics into words
  words = lyrics.split()

  # get a list of the indices of each letter in the band name in the lyrics
  band_name_indices = []
  letter_index = 0
  for i, word in enumerate(words):
    if band_name[letter_index] in word:
      band_name_indices.append(i)
      letter_index += 1
    if letter_index == len(band_name):
      break

  # return -1 if band name not fully in lyrics
  if letter_index != len(band_name):
    return -1

  lines = []
  for i in range(1, len(band_name_indices)):
    line = " ".join(words[band_name_indices[i-1]:band_name_indices[i]])
    lines.append(line)
  lines.append(words[band_name_indices[-1]])

  # get indices of the band name letters in the lines and the total buffers needed for each line
  band_name_letter_indices = []
  left_buffer = 0
  right_buffer = 0
  for i, line in enumerate(lines):
    band_name_letter_indices.append(line.index(band_name[i]))
    left_buffer = max(left_buffer, band_name_letter_indices[i])
    right_buffer = max(right_buffer, len(line) - 1 - band_name_letter_indices[i])

  # add the buffers to the lines
  for i, line in enumerate(lines):
    needed_left_buffer = left_buffer - band_name_letter_indices[i]
    needed_right_buffer = right_buffer - (len(line) - 1 - band_name_letter_indices[i])
    lines[i] = " " * needed_left_buffer + line + " " * needed_right_buffer
  
  return "\n".join(lines)


# EXAMPLES
lyrics = "...I bomb atomically, socrates, philosophies and hypotheses can't define how I be dropping these mockeries..."
band_name = "cebi"
print(arrange_lyrics_improved(lyrics, band_name))

print("\n")

lyrics = "Sometimes under the sun"
band_name = "tus"
print(arrange_lyrics_improved(lyrics, band_name))



# FOLLOW UP QUESTIONS
# 1. How do we handle the case where the band name is not in the lyrics?
# 2. How can we improve this algorithm? What is the time and space complexity?
# 3. Is there a better algorithm? What is the time and space complexity?
# 4. What tests would you write for this function?
# 5. What if there are multiple arrangements? How should we best deal with this?
# 6. How would we capitalize the band name in the output?
# 7. .....