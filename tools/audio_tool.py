import time
import numpy as np
import sounddevice as sd

class AudioTool:
    def __init__(self, voice_samples_dir=None):
        self.sample_rate = 44100
        self.base_amplitude = 0.5
        self.voice_samples = {}
        
        # Basic frequency map for 4th octave (A4 = 440Hz)
        self.note_freqs = {
            "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13,
            "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00,
            "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
            "C5": 523.25, "Rest": 0
        }
        
        self.durations = {
            "whole": 4.0,
            "half": 2.0,
            "quarter": 1.0,
            "eighth": 0.5,
            "sixteenth": 0.25
        }
        
        if voice_samples_dir:
            self.load_samples(voice_samples_dir)

    def load_samples(self, directory):
        """
        Load .wav files from directory. 
        Expected format: "C4.wav", "D4.wav", etc.
        """
        import os
        import soundfile as sf # Requires soundfile or scipy
        
        if not os.path.exists(directory):
            print(f"Warning: Voice samples directory {directory} not found.")
            return

        print(f"Loading voice samples from {directory}...")
        for filename in os.listdir(directory):
            if filename.endswith(".wav"):
                note_name = os.path.splitext(filename)[0]
                filepath = os.path.join(directory, filename)
                try:
                    data, fs = sf.read(filepath, dtype='float32')
                    # Resample if necessary (omitted for brevity, assuming 44100)
                    self.voice_samples[note_name] = data
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")

    def get_freq(self, pitch):
        return self.note_freqs.get(pitch, 0)

    def generate_tone(self, frequency, duration_sec):
        t = np.linspace(0, duration_sec, int(self.sample_rate * duration_sec), False)
        if frequency == 0:
            tone = np.zeros_like(t)
        else:
            tone = self.base_amplitude * np.sin(frequency * t * 2 * np.pi)
        return tone

    def play(self, music_data, hands=['right', 'left'], tempo_override=None, measure_range=None):
        if not music_data:
            print("No music data to play.")
            return

        # Handle legacy format (list of notes) for backward compatibility
        if 'notes' in music_data and 'measures' not in music_data:
            print("Legacy format detected. Playing as single voice.")
            self._play_legacy(music_data, tempo_override)
            return

        tempo = music_data.get('tempo')
        bpm = 120
        
        if tempo_override:
            bpm = int(tempo_override)
        elif tempo:
            try:
                import re
                match = re.search(r'\d+', str(tempo))
                if match:
                    bpm = int(match.group())
            except:
                pass
        
        beat_duration = 60.0 / bpm
        print(f"Playing at {bpm} BPM...")

        measures = music_data.get('measures', [])
        measures.sort(key=lambda x: x.get('id', 0))

        # Filter by measure range
        if measure_range:
            start_m, end_m = measure_range
            measures = [m for m in measures if start_m <= m.get('id', 0) <= end_m]

        for measure in measures:
            print(f"Playing Measure {measure.get('id')}")
            # We need to play right and left hand simultaneously for the measure.
            # This is complex because they might have different rhythms.
            # For simplicity in this iteration, we will synthesize the entire measure for each hand
            # and then mix them.
            
            # 1. Generate audio for Right Hand
            right_audio = np.zeros(0)
            if 'right' in hands:
                right_audio = self._synthesize_hand(measure.get('right_hand', []), beat_duration)

            # 2. Generate audio for Left Hand
            left_audio = np.zeros(0)
            if 'left' in hands:
                left_audio = self._synthesize_hand(measure.get('left_hand', []), beat_duration)

            # 3. Mix
            # Pad to same length
            max_len = max(len(right_audio), len(left_audio))
            if max_len == 0:
                continue
                
            mixed = np.zeros(max_len)
            if len(right_audio) > 0:
                mixed[:len(right_audio)] += right_audio
            if len(left_audio) > 0:
                mixed[:len(left_audio)] += left_audio
            
            # Normalize to prevent clipping
            max_val = np.max(np.abs(mixed))
            if max_val > 1.0:
                mixed /= max_val
            
            sd.play(mixed, self.sample_rate)
            sd.wait()

    def _synthesize_hand(self, events, beat_duration):
        hand_audio = np.array([])
        
        for event in events:
            notes = event.get('notes', [])
            duration_str = event.get('duration', 'quarter')
            rel_duration = self.durations.get(duration_str, 1.0)
            duration_sec = rel_duration * beat_duration
            
            # Generate audio for this event (chord or single note)
            event_audio = np.zeros(int(self.sample_rate * duration_sec))
            
            for pitch in notes:
                if pitch == "Rest":
                    continue
                
                if pitch in self.voice_samples:
                    sample = self.voice_samples[pitch]
                    # Simple mixing: add to event_audio (truncating sample if too long)
                    # Ideally we should handle sample duration better
                    l = min(len(sample), len(event_audio))
                    event_audio[:l] += sample[:l]
                else:
                    freq = self.get_freq(pitch)
                    tone = self.generate_tone(freq, duration_sec)
                    event_audio += tone
            
            hand_audio = np.concatenate([hand_audio, event_audio])
            
        return hand_audio

    def _play_legacy(self, music_data, tempo_override=None):
        # ... (Previous implementation for backward compatibility)
        tempo = music_data.get('tempo')
        bpm = 120
        if tempo_override:
            bpm = int(tempo_override)
        elif tempo:
            try:
                import re
                match = re.search(r'\d+', str(tempo))
                if match:
                    bpm = int(match.group())
            except:
                pass
        
        beat_duration = 60.0 / bpm
        
        for note in music_data['notes']:
            pitch = note.get('pitch', 'Rest')
            duration_str = note.get('duration', 'quarter')
            rel_duration = self.durations.get(duration_str, 1.0)
            duration_sec = rel_duration * beat_duration
            
            if pitch in self.voice_samples:
                sample = self.voice_samples[pitch]
                sd.play(sample, self.sample_rate)
            else:
                freq = self.get_freq(pitch)
                tone = self.generate_tone(freq, duration_sec)
                sd.play(tone, self.sample_rate)
            
            sd.sleep(int(duration_sec * 1000))
            sd.stop()
