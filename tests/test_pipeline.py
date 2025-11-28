import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.correction_tool import CorrectionTool
from tools.audio_tool import AudioTool

class TestPipeline(unittest.TestCase):
    def test_correction_tool(self):
        tool = CorrectionTool()
        data = {"key": "C Major", "notes": []}
        # Mock input to skip interaction
        with patch('builtins.input', return_value='p'):
            result = tool.review_and_correct(data)
        self.assertEqual(result, data)

    def test_audio_tool_generation(self):
        tool = AudioTool()
        freq = tool.get_freq("A4")
        self.assertEqual(freq, 440.0)
        
        # Test tone generation (check shape)
        tone = tool.generate_tone(440.0, 1.0)
        self.assertEqual(len(tone), 44100) # 1 sec at 44100Hz

    @patch('sounddevice.play')
    @patch('sounddevice.wait')
    def test_audio_playback(self, mock_wait, mock_play):
        tool = AudioTool()
        data = {
            "tempo": "120",
            "notes": [
                {"pitch": "C4", "duration": "quarter"},
                {"pitch": "Rest", "duration": "quarter"}
            ]
        }
        tool.play(data)
        self.assertEqual(mock_play.call_count, 2)

if __name__ == '__main__':
    unittest.main()
