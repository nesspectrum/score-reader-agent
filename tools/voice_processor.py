import os
from pydub import AudioSegment
from pydub.silence import split_on_silence

class VoiceProcessor:
    def __init__(self, silence_thresh=-40, min_silence_len=500, keep_silence=100):
        """
        :param silence_thresh: Threshold in dBFS to consider as silence.
        :param min_silence_len: Minimum length of silence in ms to be used for a split.
        :param keep_silence: Amount of silence to leave at the beginning and end of each chunk in ms.
        """
        self.silence_thresh = silence_thresh
        self.min_silence_len = min_silence_len
        self.keep_silence = keep_silence

    def process_voice_file(self, input_file, output_dir, note_names):
        """
        Splits a single audio file into multiple chunks and saves them as individual note files.
        
        :param input_file: Path to the source .wav file (e.g., "scale.wav").
        :param output_dir: Directory to save the extracted notes.
        :param note_names: List of note names to assign to the chunks in order (e.g., ["C4", "D4", "E4"]).
        """
        if not os.path.exists(input_file):
            print(f"Error: Input file {input_file} not found.")
            return False

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Loading {input_file}...")
        try:
            audio = AudioSegment.from_wav(input_file)
        except Exception as e:
            print(f"Error loading audio: {e}")
            return False

        print("Splitting audio on silence...")
        chunks = split_on_silence(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            keep_silence=self.keep_silence
        )

        print(f"Found {len(chunks)} chunks.")
        
        if len(chunks) != len(note_names):
            print(f"Warning: Found {len(chunks)} chunks but expected {len(note_names)} notes.")
            print("Saving as many as possible matching the order...")

        for i, chunk in enumerate(chunks):
            if i < len(note_names):
                note_name = note_names[i]
                output_path = os.path.join(output_dir, f"{note_name}.wav")
                print(f"Saving {note_name} to {output_path}")
                chunk.export(output_path, format="wav")
            else:
                print(f"Skipping extra chunk {i+1}")

        return True
