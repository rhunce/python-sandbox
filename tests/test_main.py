import unittest
from src.main import arrange_lyrics, band_name

class TestArrangeLyrics(unittest.TestCase):
    def test_main_runs(self):
        lyrics = "...I bomb atomically, socrates, philosophies and hypotheses can't define how I be dropping these mockeries..."
        band_name = "miee"
        self.assertEqual(arrange_lyrics(lyrics, band_name), 5)

if __name__ == "__main__":
    unittest.main()
