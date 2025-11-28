import unittest
import os
import sys
import numpy as np
from pydub import AudioSegment
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.voice_processor import VoiceProcessor

class TestVoiceProcessor(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_voice_output"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
        # Create a synthetic wav file with silence
        # 1 sec tone, 1 sec silence, 1 sec tone
        self.sample_rate = 44100
        t = np.linspace(0, 1.0, 44100, False)
        tone = 0.5 * np.sin(440 * t * 2 * np.pi)
        silence = np.zeros(44100)
        
        # Combine: Tone - Silence - Tone
        audio_data = np.concatenate([tone, silence, tone])
        
        # Convert to 16-bit PCM for pydub
        audio_data_int = (audio_data * 32767).astype(np.int16)
        
        self.audio_segment = AudioSegment(
            audio_data_int.tobytes(), 
            frame_rate=44100,
            sample_width=2, 
            channels=1
        )
        
        self.input_file = "test_scale.wav"
        self.audio_segment.export(self.input_file, format="wav")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.input_file):
            os.remove(self.input_file)

    def test_split_voice(self):
        processor = VoiceProcessor(min_silence_len=500, silence_thresh=-40)
        notes = ["Note1", "Note2"]
        
        success = processor.process_voice_file(self.input_file, self.test_dir, notes)
        self.assertTrue(success)
        
        # Check if files exist
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Note1.wav")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Note2.wav")))

if __name__ == '__main__':
    unittest.main()
