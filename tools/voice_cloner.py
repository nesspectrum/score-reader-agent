import os
import numpy as np
import librosa
import soundfile as sf

class VoiceCloner:
    def __init__(self, output_dir="voice_samples"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Target frequencies for 4th octave and some of 5th
        self.note_freqs = {
            "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,
            "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
            "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.25, "F5": 698.46, "F#5": 739.99, "G5": 783.99
        }

    def clone_voice(self, input_file):
        """
        Takes an input audio file (e.g., user saying "Ah"), detects its pitch,
        and generates pitch-shifted samples for other notes.
        """
        if not os.path.exists(input_file):
            print(f"Error: Input file {input_file} not found.")
            return False

        print(f"Loading {input_file}...")
        try:
            y, sr = librosa.load(input_file, sr=None)
        except Exception as e:
            print(f"Error loading audio: {e}")
            return False

        # Detect pitch (Fundamental Frequency - F0)
        print("Detecting pitch...")
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        
        # Get the median pitch of voiced segments
        voiced_f0 = f0[voiced_flag]
        if len(voiced_f0) == 0:
            print("Error: Could not detect pitch in the audio.")
            return False
            
        base_freq = np.median(voiced_f0)
        base_note = librosa.hz_to_note(base_freq)
        print(f"Detected base frequency: {base_freq:.2f} Hz ({base_note})")

        print("Generating samples...")
        for note, target_freq in self.note_freqs.items():
            # Calculate semitone shift
            # n_steps = 12 * log2(target / base)
            n_steps = 12 * np.log2(target_freq / base_freq)
            
            # Shift pitch
            y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)
            
            # Save
            output_path = os.path.join(self.output_dir, f"{note}.wav")
            sf.write(output_path, y_shifted, sr)
            # print(f"Generated {note}")

        print(f"Voice cloning complete. Samples saved to '{self.output_dir}'.")
        return True
