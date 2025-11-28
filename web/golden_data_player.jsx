// Enhanced React Music Player for Golden Data Generation
// Based on json-music-player_v35.tsx with editing capabilities

const { useState, useRef, useEffect } = React;
const { Play, Pause, Square, Upload, Save, Edit2, Check, X } = lucideReact;

const GoldenDataPlayer = () => {
  const [musicData, setMusicData] = useState(null);
  const [originalData, setOriginalData] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState(null);
  const [debugLog, setDebugLog] = useState([]);
  const [showTextInput, setShowTextInput] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [tempoMultiplier, setTempoMultiplier] = useState(1.0);
  const [playMode, setPlayMode] = useState('both');
  const [isEditing, setIsEditing] = useState(false);
  const [testId, setTestId] = useState('');
  const [testCases, setTestCases] = useState([]);
  const [comparison, setComparison] = useState(null);
  const audioContextRef = useRef(null);
  const oscillatorsRef = useRef([]);

  // Load test cases on mount
  useEffect(() => {
    loadTestCases();
  }, []);

  const loadTestCases = async () => {
    try {
      const response = await fetch('/api/test-cases');
      const data = await response.json();
      if (data.status === 'success') {
        setTestCases(data.test_cases);
      }
    } catch (e) {
      addDebugLog(`Error loading test cases: ${e.message}`);
    }
  };

  const loadExtraction = async (filePath, testIdParam = null) => {
    try {
      const response = await fetch('/api/load-extraction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath, test_id: testIdParam })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setMusicData(data.extracted_data);
        setOriginalData(JSON.parse(JSON.stringify(data.extracted_data)));
        if (data.test_id) setTestId(data.test_id);
        setError(null);
        addDebugLog(`Loaded extraction from ${filePath}`);
      }
    } catch (e) {
      setError(`Error loading extraction: ${e.message}`);
      addDebugLog(`Error: ${e.message}`);
    }
  };

  const loadTestCase = async (testIdParam) => {
    try {
      const response = await fetch(`/api/test-case/${testIdParam}`);
      const data = await response.json();
      if (data.status === 'success') {
        const tc = data.test_case;
        setMusicData(tc.golden_data || tc.extracted_data);
        setOriginalData(tc.extracted_data);
        setTestId(testIdParam);
        
        // Load comparison if golden exists
        if (tc.has_golden) {
          const compResponse = await fetch(`/api/compare/${testIdParam}`);
          const compData = await compResponse.json();
          if (compData.status === 'success') {
            setComparison(compData.comparison);
          }
        }
        
        setError(null);
        addDebugLog(`Loaded test case ${testIdParam}`);
      }
    } catch (e) {
      setError(`Error loading test case: ${e.message}`);
    }
  };

  const saveGoldenData = async () => {
    if (!testId) {
      setError('Please set a test ID first');
      return;
    }

    try {
      const response = await fetch('/api/save-golden', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          test_id: testId,
          golden_data: musicData,
          corrections: calculateCorrections(),
          notes: prompt('Notes about corrections (optional):') || null
        })
      });
      const data = await response.json();
      if (data.status === 'success') {
        addDebugLog(`Golden data saved for ${testId}`);
        setOriginalData(JSON.parse(JSON.stringify(musicData)));
        setIsEditing(false);
        await loadTestCases();
        alert('Golden data saved successfully!');
      }
    } catch (e) {
      setError(`Error saving golden data: ${e.message}`);
    }
  };

  const calculateCorrections = () => {
    if (!originalData) return {};
    const corrections = {};
    if (originalData.key !== musicData.key) corrections.key = musicData.key;
    if (originalData.tempo !== musicData.tempo) corrections.tempo = musicData.tempo;
    if (originalData.composer !== musicData.composer) corrections.composer = musicData.composer;
    if (originalData.piece_name !== musicData.piece_name) corrections.piece_name = musicData.piece_name;
    return corrections;
  };

  const addDebugLog = (message) => {
    const logMessage = typeof message === 'string' ? message : JSON.stringify(message);
    setDebugLog(prev => [...prev.slice(-49), `${new Date().toLocaleTimeString()}: ${logMessage}`]);
    console.log(logMessage);
  };

  // Note frequency mapping (A4 = 440Hz)
  const getFrequency = (note) => {
    if (!note || note === 'rest' || note.toLowerCase() === 'rest') return 0;
    
    const noteFrequencies = {
      'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
    };
    
    const match = note.match(/([A-G])(#|b)?(\d+)/);
    if (!match) return 0;
    
    const [, noteName, accidental, octave] = match;
    let semitones = noteFrequencies[noteName];
    
    if (accidental === '#') semitones += 1;
    if (accidental === 'b') semitones -= 1;
    
    const octaveNum = parseInt(octave);
    const A4 = 440;
    const C0 = A4 * Math.pow(2, -4.75);
    
    const totalSemitones = octaveNum * 12 + semitones;
    return C0 * Math.pow(2, totalSemitones / 12);
  };

  const parseDuration = (durationStr) => {
    const durations = {
      'whole': 4, 'half': 2, 'quarter': 1,
      'eighth': 0.5, 'sixteenth': 0.25, 'thirty_second': 0.125,
      'dotted whole': 6, 'dotted half': 3, 'dotted quarter': 1.5,
      'dotted eighth': 0.75, 'dotted sixteenth': 0.375
    };
    
    if (Array.isArray(durationStr)) {
      return durationStr.reduce((sum, d) => sum + parseDuration(d), 0);
    }
    
    durationStr = String(durationStr).trim().toLowerCase();
    
    if (durations[durationStr]) {
      return durations[durationStr];
    }
    
    if (durationStr.includes('dotted')) {
      const baseStr = durationStr.replace('dotted', '').trim();
      const baseValue = durations[baseStr] || 0;
      return baseValue * 1.5;
    }
    
    if (durationStr.endsWith('.')) {
      const baseStr = durationStr.slice(0, -1).trim();
      const baseValue = durations[baseStr] || 0;
      return baseValue * 1.5;
    }
    
    if (durationStr.includes(',')) {
      return durationStr.split(',').reduce((sum, part) => sum + parseDuration(part.trim()), 0);
    }
    
    if (durationStr.includes('*')) {
      const [num, type] = durationStr.split('*').map(s => s.trim());
      return parseInt(num) * parseDuration(type);
    }
    
    const numberWords = {
      'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
      'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
      'eleven': 11, 'twelve': 12
    };
    
    const words = durationStr.split(/\s+/);
    if (words.length >= 2 && numberWords[words[0]]) {
      const multiplier = numberWords[words[0]];
      const type = words.slice(1).join(' ');
      return multiplier * parseDuration(type);
    }
    
    return durations[durationStr] || 1;
  };

  const scheduleNote = (frequency, startTime, duration, audioContext, volume = 0.15) => {
    if (frequency === 0) {
      addDebugLog(`Rest scheduled at ${startTime.toFixed(3)}s for ${duration.toFixed(3)}s`);
      return null;
    }
    
    try {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = frequency;
      oscillator.type = 'sine';
      
      const attackTime = Math.min(0.02, duration * 0.1);
      const releaseTime = Math.min(0.1, duration * 0.3);
      
      gainNode.gain.setValueAtTime(0, startTime);
      gainNode.gain.linearRampToValueAtTime(volume, startTime + attackTime);
      
      if (duration > attackTime + releaseTime) {
        gainNode.gain.setValueAtTime(volume * 0.7, startTime + attackTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
      } else {
        gainNode.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
      }
      
      oscillator.start(startTime);
      oscillator.stop(startTime + duration);
      
      addDebugLog(`Note scheduled: ${frequency.toFixed(2)}Hz at ${startTime.toFixed(3)}s for ${duration.toFixed(3)}s`);
      
      return oscillator;
    } catch (e) {
      addDebugLog(`ERROR scheduling note: ${e.message}`);
      console.error('Error scheduling note:', e);
      return null;
    }
  };

  const playMusicData = async () => {
    if (!musicData) return;
    
    try {
      setError(null);
      setDebugLog([]);
      addDebugLog('=== Starting Playback ===');
      
      stopPlayback();
      
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;
      
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
        addDebugLog('AudioContext was suspended, resumed it');
      }
      
      addDebugLog(`AudioContext created, state: ${audioContext.state}`);
      
      let bpm = 120;
      if (musicData.tempo) {
        if (typeof musicData.tempo === 'string' || typeof musicData.tempo === 'number') {
          bpm = parseInt(musicData.tempo);
        } else if (typeof musicData.tempo === 'object') {
          const tempoKeys = Object.keys(musicData.tempo);
          if (tempoKeys.length > 0) {
            const noteType = tempoKeys[0];
            const tempoValue = parseInt(musicData.tempo[noteType]);
            
            if (noteType === 'eighth') {
              bpm = tempoValue / 2;
            } else if (noteType === 'sixteenth') {
              bpm = tempoValue / 4;
            } else if (noteType === 'half') {
              bpm = tempoValue * 2;
            } else {
              bpm = tempoValue;
            }
          }
        }
      }
      
      const beatDuration = 60 / bpm / tempoMultiplier;
      addDebugLog(`BPM: ${bpm}, Tempo multiplier: ${tempoMultiplier}x, Effective BPM: ${(bpm * tempoMultiplier).toFixed(1)}, Beat duration: ${beatDuration.toFixed(3)}s`);
      
      let currentTime = audioContext.currentTime + 0.1;
      const oscillators = [];
      
      addDebugLog(`Starting time: ${currentTime.toFixed(3)}s`);
      
      for (const measure of musicData.measures || []) {
        const measureStartTime = currentTime;
        addDebugLog(`\n--- Measure ${measure.id} starts at ${measureStartTime.toFixed(3)}s ---`);
        
        let rhTime = measureStartTime;
        if (playMode === 'both' || playMode === 'right') {
          addDebugLog('RIGHT HAND:');
          for (const noteData of measure.right_hand || []) {
            const notes = noteData.notes || [];
            const duration = parseDuration(noteData.duration) * beatDuration;
            
            addDebugLog(`  Notes: [${notes.join(', ')}] Duration: ${noteData.duration} = ${duration.toFixed(3)}s`);
            
            for (const note of notes) {
              const freq = getFrequency(note);
              const osc = scheduleNote(freq, rhTime, duration, audioContext, 0.12);
              if (osc) oscillators.push(osc);
            }
            
            rhTime += duration;
          }
          addDebugLog(`Right hand ends at ${rhTime.toFixed(3)}s`);
        } else {
          addDebugLog('RIGHT HAND: Skipped');
          for (const noteData of measure.right_hand || []) {
            const duration = parseDuration(noteData.duration) * beatDuration;
            rhTime += duration;
          }
        }
        
        let lhTime = measureStartTime;
        if (playMode === 'both' || playMode === 'left') {
          addDebugLog('LEFT HAND:');
          let i = 0;
        
          while (i < (measure.left_hand || []).length) {
            const noteData = measure.left_hand[i];
            const notes = noteData.notes || [];
            const duration = noteData.duration;
            
            addDebugLog(`  Entry ${i}: [${notes.join(', ')}] Duration: ${JSON.stringify(duration)}`);
            
            if (notes.length > 1 && Array.isArray(duration)) {
              const actualNotes = notes.filter(n => n.toLowerCase() !== 'rest');
              const restIndex = notes.findIndex(n => n.toLowerCase() === 'rest');
              
              if (actualNotes.length > 0 && restIndex >= 0 && restIndex < duration.length) {
                const sustainedDuration = parseDuration(duration[0]) * beatDuration;
                
                for (const note of actualNotes) {
                  const freq = getFrequency(note);
                  addDebugLog(`    Sustained: ${note} for ${sustainedDuration.toFixed(3)}s`);
                  
                  const osc1 = scheduleNote(freq, lhTime, sustainedDuration, audioContext, 0.15);
                  if (osc1) oscillators.push(osc1);
                }
                
                const gapDuration = parseDuration(duration[restIndex]) * beatDuration;
                let fillingTime = lhTime + gapDuration;
                
                addDebugLog(`    Gap duration: ${gapDuration.toFixed(3)}s, filling notes start at ${fillingTime.toFixed(3)}s`);
                
                i++;
                while (i < measure.left_hand.length) {
                  const nextNote = measure.left_hand[i];
                  
                  if (nextNote.notes.length > 1 && Array.isArray(nextNote.duration)) {
                    lhTime = fillingTime;
                    addDebugLog(`    Next overlapping pattern detected, moving to ${lhTime.toFixed(3)}s`);
                    break;
                  }
                  
                  const fillDuration = parseDuration(nextNote.duration) * beatDuration;
                  
                  for (const note of nextNote.notes) {
                    const fillFreq = getFrequency(note);
                    addDebugLog(`    Filling: ${note} at ${fillingTime.toFixed(3)}s for ${fillDuration.toFixed(3)}s`);
                    
                    const osc2 = scheduleNote(fillFreq, fillingTime, fillDuration, audioContext, 0.15);
                    if (osc2) oscillators.push(osc2);
                  }
                  
                  fillingTime += fillDuration;
                  i++;
                  
                  if (fillingTime >= lhTime + sustainedDuration) {
                    lhTime = fillingTime;
                    addDebugLog(`    Gap filled, moving to ${lhTime.toFixed(3)}s`);
                    break;
                  }
                }
              } else {
                const chordDuration = parseDuration(duration[0]) * beatDuration;
                
                for (const note of actualNotes) {
                  const freq = getFrequency(note);
                  addDebugLog(`    Chord note: ${note} for ${chordDuration.toFixed(3)}s`);
                  
                  const osc = scheduleNote(freq, lhTime, chordDuration, audioContext, 0.15);
                  if (osc) oscillators.push(osc);
                }
                
                lhTime += chordDuration;
                i++;
              }
            } else {
              const noteDuration = parseDuration(duration) * beatDuration;
              
              for (const note of notes) {
                if (note.toLowerCase() !== 'rest') {
                  const freq = getFrequency(note);
                  addDebugLog(`    Sequential: ${note} for ${noteDuration.toFixed(3)}s`);
                  
                  const osc = scheduleNote(freq, lhTime, noteDuration, audioContext, 0.15);
                  if (osc) oscillators.push(osc);
                }
              }
              
              lhTime += noteDuration;
              i++;
            }
          }
          addDebugLog(`Left hand ends at ${lhTime.toFixed(3)}s`);
        } else {
          addDebugLog('LEFT HAND: Skipped');
          let i = 0;
          while (i < (measure.left_hand || []).length) {
            const noteData = measure.left_hand[i];
            const notes = noteData.notes || [];
            const duration = noteData.duration;
            
            if (notes.length > 1 && Array.isArray(duration)) {
              const actualNotes = notes.filter(n => n.toLowerCase() !== 'rest');
              const restIndex = notes.findIndex(n => n.toLowerCase() === 'rest');
              
              if (actualNotes.length > 0 && restIndex >= 0 && restIndex < duration.length) {
                const sustainedDuration = parseDuration(duration[0]) * beatDuration;
                const gapDuration = parseDuration(duration[restIndex]) * beatDuration;
                let fillingTime = lhTime + gapDuration;
                
                i++;
                while (i < measure.left_hand.length) {
                  const nextNote = measure.left_hand[i];
                  if (nextNote.notes.length > 1 && Array.isArray(nextNote.duration)) {
                    lhTime = fillingTime;
                    break;
                  }
                  const fillDuration = parseDuration(nextNote.duration) * beatDuration;
                  fillingTime += fillDuration;
                  i++;
                  if (fillingTime >= lhTime + sustainedDuration) {
                    lhTime = fillingTime;
                    break;
                  }
                }
              } else {
                const chordDuration = parseDuration(duration[0]) * beatDuration;
                lhTime += chordDuration;
                i++;
              }
            } else {
              const noteDuration = parseDuration(duration) * beatDuration;
              lhTime += noteDuration;
              i++;
            }
          }
        }
        
        currentTime = Math.max(rhTime, lhTime);
        addDebugLog(`Measure ends at ${currentTime.toFixed(3)}s\n`);
      }
      
      oscillatorsRef.current = oscillators;
      addDebugLog(`\nTotal oscillators scheduled: ${oscillators.length}`);
      addDebugLog(`Total duration: ${(currentTime - audioContext.currentTime).toFixed(3)}s`);
      
      setIsPlaying(true);
      
      const totalDuration = (currentTime - audioContext.currentTime) * 1000;
      addDebugLog(`Will stop playback in ${totalDuration.toFixed(0)}ms`);
      
      setTimeout(() => {
        addDebugLog('Playback finished');
        setIsPlaying(false);
      }, totalDuration + 100);
      
    } catch (e) {
      const errorMsg = 'Playback error: ' + e.message;
      setError(errorMsg);
      addDebugLog(`ERROR: ${errorMsg}`);
      console.error('Playback error:', e);
      setIsPlaying(false);
    }
  };

  const stopPlayback = () => {
    oscillatorsRef.current.forEach(osc => {
      try {
        osc.stop();
      } catch (e) {
        // Already stopped
      }
    });
    oscillatorsRef.current = [];
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    setIsPlaying(false);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        let jsonText = e.target.result;
        jsonText = jsonText.replace(/,(\s*[}\]])/g, '$1');
        
        const json = JSON.parse(jsonText);
        setMusicData(json);
        setOriginalData(JSON.parse(JSON.stringify(json)));
        setError(null);
        addDebugLog('File loaded successfully');
      } catch (error) {
        setError('Error parsing JSON: ' + error.message);
        addDebugLog('Error parsing JSON: ' + error.message);
      }
    };
    reader.readAsText(file);
  };

  const handleTextInput = (text) => {
    try {
      let jsonText = text.replace(/,(\s*[}\]])/g, '$1');
      const json = JSON.parse(jsonText);
      setMusicData(json);
      setOriginalData(JSON.parse(JSON.stringify(json)));
      setError(null);
      addDebugLog('JSON loaded from text input');
    } catch (error) {
      setError('Error parsing JSON: ' + error.message);
      addDebugLog('Error parsing JSON: ' + error.message);
    }
  };

  const handleEditJSON = () => {
    if (isEditing) {
      // Save edited JSON
      try {
        const edited = JSON.parse(textInput);
        setMusicData(edited);
        setIsEditing(false);
        addDebugLog('JSON edited and applied');
      } catch (e) {
        setError('Invalid JSON: ' + e.message);
      }
    } else {
      // Enter edit mode
      setTextInput(JSON.stringify(musicData, null, 2));
      setIsEditing(true);
    }
  };

  const hasChanges = () => {
    if (!originalData || !musicData) return false;
    return JSON.stringify(originalData) !== JSON.stringify(musicData);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-2xl">
          <h1 className="text-4xl font-bold text-white mb-2 text-center">
            🎵 Golden Data Generator
          </h1>
          <p className="text-white/70 text-center mb-6">ScoreOrchestrator - Human-in-the-Loop Evaluation Tool</p>
          
          {/* Test Case Management */}
          <div className="mb-6 bg-white/10 rounded-xl p-4">
            <h3 className="text-xl font-bold text-white mb-3">Test Case Management</h3>
            <div className="flex gap-3 mb-3">
              <input
                type="text"
                placeholder="Test ID (e.g., test_001)"
                value={testId}
                onChange={(e) => setTestId(e.target.value)}
                className="flex-1 px-4 py-2 bg-white/20 text-white rounded-lg border-2 border-white/30 focus:border-white/60 outline-none"
              />
              <button
                onClick={() => loadTestCase(testId)}
                disabled={!testId}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-all disabled:opacity-50"
              >
                Load Test Case
              </button>
            </div>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Path to extracted JSON (e.g., library/xxx.json)"
                id="extraction-path"
                className="flex-1 px-4 py-2 bg-white/20 text-white rounded-lg border-2 border-white/30 focus:border-white/60 outline-none"
              />
              <button
                onClick={() => {
                  const path = document.getElementById('extraction-path').value;
                  if (path) loadExtraction(path, testId || null);
                }}
                className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-all"
              >
                Load Extraction
              </button>
            </div>
            
            {testCases.length > 0 && (
              <div className="mt-3">
                <p className="text-white/80 text-sm mb-2">Available Test Cases:</p>
                <div className="flex flex-wrap gap-2">
                  {testCases.map(tc => (
                    <button
                      key={tc.test_id}
                      onClick={() => loadTestCase(tc.test_id)}
                      className={`px-3 py-1 rounded text-sm ${
                        tc.has_golden
                          ? 'bg-green-500/30 text-green-200 border border-green-500'
                          : 'bg-white/20 text-white border border-white/30'
                      } hover:bg-white/30 transition-all`}
                    >
                      {tc.test_id} {tc.has_golden ? '✓' : ''}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Comparison View */}
          {comparison && (
            <div className="mb-6 bg-yellow-500/20 border border-yellow-500/50 rounded-xl p-4">
              <h3 className="text-lg font-bold text-yellow-200 mb-2">Comparison: Extracted vs Golden</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-yellow-200">Key Match:</span> {comparison.key_match ? '✓' : '✗'}
                </div>
                <div>
                  <span className="text-yellow-200">Tempo Match:</span> {comparison.tempo_match ? '✓' : '✗'}
                </div>
                <div>
                  <span className="text-yellow-200">Composer Match:</span> {comparison.composer_match ? '✓' : '✗'}
                </div>
                <div>
                  <span className="text-yellow-200">Piece Name Match:</span> {comparison.piece_name_match ? '✓' : '✗'}
                </div>
                <div>
                  <span className="text-yellow-200">Measures:</span> {comparison.extracted_measures} vs {comparison.golden_measures}
                </div>
                <div>
                  <span className="text-yellow-200">Accuracy:</span> {(comparison.accuracy_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}

          {/* JSON Editor */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <button
                onClick={() => setShowTextInput(!showTextInput)}
                className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white font-semibold rounded-lg transition-all"
              >
                {showTextInput ? 'Hide' : 'Show'} JSON Editor
              </button>
              {musicData && (
                <div className="flex gap-2">
                  <button
                    onClick={handleEditJSON}
                    className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-all flex items-center gap-2"
                  >
                    {isEditing ? <Check size={18} /> : <Edit2 size={18} />}
                    {isEditing ? 'Save Edit' : 'Edit JSON'}
                  </button>
                  {hasChanges() && (
                    <button
                      onClick={saveGoldenData}
                      disabled={!testId}
                      className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-all flex items-center gap-2 disabled:opacity-50"
                    >
                      <Save size={18} />
                      Save as Golden
                    </button>
                  )}
                </div>
              )}
            </div>
            
            {showTextInput && (
              <div className="space-y-3">
                <textarea
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Paste or edit your JSON here..."
                  className="w-full h-64 p-4 bg-white/10 text-white rounded-lg font-mono text-sm border-2 border-white/30 focus:border-white/60 outline-none"
                  readOnly={!isEditing}
                />
                {!isEditing && (
                  <button
                    onClick={() => handleTextInput(textInput)}
                    className="w-full px-4 py-3 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-all"
                  >
                    Load JSON from Text
                  </button>
                )}
              </div>
            )}
          </div>
          
          {/* File Upload */}
          <div className="mb-8">
            <label className="flex items-center justify-center gap-3 px-6 py-4 bg-white/20 hover:bg-white/30 rounded-xl cursor-pointer transition-all border-2 border-white/30">
              <Upload className="text-white" size={24} />
              <span className="text-white font-semibold">Upload JSON Music File</span>
              <input
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>
          
          {error && (
            <div className="mb-6 p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-200">
              {error}
            </div>
          )}
          
          {/* Music Player UI - Same as original */}
          {musicData && (
            <div className="space-y-6">
              <div className="bg-white/10 rounded-xl p-6">
                <h2 className="text-2xl font-bold text-white mb-3">
                  {musicData.piece_name || musicData.title || 'Untitled'}
                </h2>
                <div className="grid grid-cols-2 gap-4 text-white/80">
                  {musicData.composer && (
                    <div>
                      <span className="font-semibold">Composer:</span> {String(musicData.composer)}
                    </div>
                  )}
                  {musicData.tempo && (
                    <div>
                      <span className="font-semibold">Tempo:</span> ♩ = {
                        typeof musicData.tempo === 'object' 
                          ? `${Object.keys(musicData.tempo)[0]} = ${String(Object.values(musicData.tempo)[0])}`
                          : String(musicData.tempo)
                      }
                    </div>
                  )}
                  {musicData.key && (
                    <div>
                      <span className="font-semibold">Key:</span> {String(musicData.key)}
                    </div>
                  )}
                  {musicData.time_signature && (
                    <div>
                      <span className="font-semibold">Time:</span> {String(musicData.time_signature?.numerator || 4)}/{String(musicData.time_signature?.denominator || 4)}
                    </div>
                  )}
                </div>
                {musicData.description && (
                  <div className="mt-3 text-white/80">
                    <span className="font-semibold">Description:</span> {String(musicData.description)}
                  </div>
                )}
                {musicData.measures && (
                  <div className="mt-3 text-white/80">
                    <span className="font-semibold">Measures:</span> {String(musicData.measures?.length || 0)}
                  </div>
                )}
              </div>
              
              <div className="bg-white/10 rounded-xl p-6 space-y-4">
                <h3 className="text-xl font-bold text-white mb-3">Playback Settings</h3>
                
                <div>
                  <label className="block text-white font-semibold mb-2">
                    Tempo: {(tempoMultiplier * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0.25"
                    max="2"
                    step="0.05"
                    value={tempoMultiplier}
                    onChange={(e) => setTempoMultiplier(parseFloat(e.target.value))}
                    className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
                    disabled={isPlaying}
                  />
                  <div className="flex justify-between text-white/60 text-sm mt-1">
                    <span>25% (Slower)</span>
                    <span>100% (Normal)</span>
                    <span>200% (Faster)</span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-white font-semibold mb-2">Play Mode:</label>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setPlayMode('both')}
                      disabled={isPlaying}
                      className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all ${
                        playMode === 'both'
                          ? 'bg-blue-500 text-white'
                          : 'bg-white/20 text-white/80 hover:bg-white/30'
                      } ${isPlaying ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      Both Hands
                    </button>
                    <button
                      onClick={() => setPlayMode('right')}
                      disabled={isPlaying}
                      className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all ${
                        playMode === 'right'
                          ? 'bg-blue-500 text-white'
                          : 'bg-white/20 text-white/80 hover:bg-white/30'
                      } ${isPlaying ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      Right Hand
                    </button>
                    <button
                      onClick={() => setPlayMode('left')}
                      disabled={isPlaying}
                      className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all ${
                        playMode === 'left'
                          ? 'bg-blue-500 text-white'
                          : 'bg-white/20 text-white/80 hover:bg-white/30'
                      } ${isPlaying ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      Left Hand
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-4 justify-center">
                {!isPlaying ? (
                  <button
                    onClick={playMusicData}
                    className="flex items-center gap-3 px-8 py-4 bg-green-500 hover:bg-green-600 text-white font-bold rounded-xl transition-all shadow-lg"
                  >
                    <Play size={24} />
                    Play
                  </button>
                ) : (
                  <button
                    onClick={stopPlayback}
                    className="flex items-center gap-3 px-8 py-4 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl transition-all shadow-lg"
                  >
                    <Square size={24} />
                    Stop
                  </button>
                )}
              </div>
            </div>
          )}
          
          {!musicData && (
            <div className="text-center text-white/60 py-12">
              <p className="text-xl">Load a test case or upload JSON to get started</p>
            </div>
          )}
          
          {debugLog.length > 0 && (
            <div className="mt-6 bg-black/40 rounded-xl p-4 max-h-96 overflow-y-auto">
              <h3 className="text-white font-bold mb-2">Debug Log:</h3>
              <div className="font-mono text-xs text-green-300 space-y-1">
                {debugLog.map((log, i) => (
                  <div key={i} className="whitespace-pre-wrap">{log}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Render the component
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<GoldenDataPlayer />);

