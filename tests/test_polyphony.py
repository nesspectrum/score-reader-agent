import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.audio_tool import AudioTool

class TestPolyphony(unittest.TestCase):
    @patch('sounddevice.play')
    @patch('sounddevice.wait')
    def test_polyphony_and_hands(self, mock_wait, mock_play):
        tool = AudioTool()
        
        # New data structure
        data = {
            "key": "C Major",
            "tempo": "120",
            "measures": [
                {
                    "id": 1,
                    "right_hand": [
                        {"notes": ["C4", "E4", "G4"], "duration": "quarter"} # C Major Chord
                    ],
                    "left_hand": [
                        {"notes": ["C3"], "duration": "quarter"}
                    ]
                }
            ]
        }
        
        # Test playing both hands
        print("Testing Both Hands...")
        tool.play(data, hands=['left', 'right'])
        # Should call play once for the measure (mixed)
        self.assertEqual(mock_play.call_count, 1)
        
        # Verify the shape of the audio passed to play
        # 120 bpm -> 0.5 sec per beat (quarter)
        # 44100 * 0.5 = 22050 samples
        args, _ = mock_play.call_args
        audio_data = args[0]
        self.assertEqual(len(audio_data), 22050)
        
        mock_play.reset_mock()
        
        # Test playing only left hand
        print("Testing Left Hand...")
        tool.play(data, hands=['left'])
        self.assertEqual(mock_play.call_count, 1)
        
        mock_play.reset_mock()
        
        # Test tempo override
        print("Testing Tempo Override...")
        tool.play(data, tempo_override=60) # Slower, 1 sec per beat
        args, _ = mock_play.call_args
        audio_data = args[0]
        self.assertEqual(len(audio_data), 44100) # 1 sec

if __name__ == '__main__':
    unittest.main()
