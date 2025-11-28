import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We want to test AudioTool logic used in the interactive loop.
# The loop logic itself is in main.py, which is hard to test without refactoring.
# However, the previous test was testing AudioTool.play with measure_range.
# We don't need to mock sys.modules for that if we just import AudioTool.

from tools.audio_tool import AudioTool

class TestInteractiveAudio(unittest.TestCase):
    @patch('sounddevice.play')
    @patch('sounddevice.wait')
    def test_measure_range(self, mock_wait, mock_play):
        tool = AudioTool()
        data = {
            "tempo": "120",
            "measures": [
                {"id": 1, "right_hand": [{"notes": ["C4"], "duration": "quarter"}]},
                {"id": 2, "right_hand": [{"notes": ["D4"], "duration": "quarter"}]},
                {"id": 3, "right_hand": [{"notes": ["E4"], "duration": "quarter"}]}
            ]
        }
        
        # Test playing measure 2 only
        print("Testing Measure Range (2-2)...")
        tool.play(data, measure_range=(2, 2))
        self.assertEqual(mock_play.call_count, 1) # Should play once for measure 2
        
        mock_play.reset_mock()
        
        # Test playing range 1-2
        print("Testing Measure Range (1-2)...")
        tool.play(data, measure_range=(1, 2))
        self.assertEqual(mock_play.call_count, 2) # Measure 1 and 2

if __name__ == '__main__':
    unittest.main()
