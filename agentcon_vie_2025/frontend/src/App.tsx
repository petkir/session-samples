import { useState, useEffect, useRef } from 'react';
import './App.css';
import { useWebSocket } from './hooks/useWebSocket';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useAudioPlayer } from './hooks/useAudioPlayer';
import { GroundingFile } from './types';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [groundingFiles, setGroundingFiles] = useState<GroundingFile[]>([]);
  const [transcript, setTranscript] = useState<string>('');
  const [debugLogs, setDebugLogs] = useState<string[]>([]);
  const [showDebug, setShowDebug] = useState(false);

  const addDebugLog = (message: string) => {
    setDebugLogs(prev => [...prev.slice(-50), `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  const { sendMessage, lastMessage, readyState } = useWebSocket('/realtime', {
    onOpen: () => {
      setIsConnected(true);
      addDebugLog('WebSocket connected');
    },
    onClose: () => {
      setIsConnected(false);
      addDebugLog('WebSocket disconnected');
    },
    onError: (error) => {
      addDebugLog(`WebSocket error: ${error}`);
    }
  });

  const { startRecording, stopRecording, audioData } = useAudioRecorder();
  const { playAudio, stopAudio } = useAudioPlayer();

  // Send audio data to server
  useEffect(() => {
    if (audioData && sendMessage) {
      const message = {
        type: 'input_audio_buffer.append',
        audio: audioData
      };
      sendMessage(JSON.stringify(message));
    }
  }, [audioData, sendMessage]);

  // Handle incoming messages
  useEffect(() => {
    if (!lastMessage) return;

    try {
      const message = JSON.parse(lastMessage);
      addDebugLog(`Received: ${message.type}`);

      switch (message.type) {
        case 'session.created':
          addDebugLog('Session created');
          // Send session update with turn detection
          const sessionUpdate = {
            type: 'session.update',
            session: {
              turn_detection: {
                type: 'server_vad'
              }
            }
          };
          sendMessage(JSON.stringify(sessionUpdate));
          break;

        case 'response.audio.delta':
          if (message.delta) {
            playAudio(message.delta);
          }
          break;

        case 'response.audio_transcript.delta':
          if (message.delta) {
            setTranscript(prev => prev + message.delta);
          }
          break;

        case 'input_audio_buffer.speech_started':
          stopAudio();
          setTranscript('');
          addDebugLog('Speech detected');
          break;

        case 'extension.middle_tier_tool_response':
          addDebugLog(`Tool response: ${message.tool_name}`);
          if (message.tool_result) {
            try {
              const result = JSON.parse(message.tool_result);
              if (result.sources) {
                setGroundingFiles(result.sources);
                addDebugLog(`Citations: ${result.sources.length} sources`);
              }
            } catch (e) {
              addDebugLog(`Tool result: ${message.tool_result}`);
            }
          }
          break;

        case 'error':
          addDebugLog(`Error: ${message.error?.message || 'Unknown error'}`);
          break;
      }
    } catch (e) {
      console.error('Failed to parse message:', e);
    }
  }, [lastMessage, sendMessage, playAudio, stopAudio]);

  const handleToggleRecording = async () => {
    if (isRecording) {
      stopRecording();
      setIsRecording(false);
    } else {
      await startRecording();
      setIsRecording(true);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎙️ VoiceRAG + Tools</h1>
        <p>Talk to your data with AI-powered voice search</p>
        <div className="connection-status">
          {isConnected ? (
            <span className="status-connected">● Connected</span>
          ) : (
            <span className="status-disconnected">● Disconnected</span>
          )}
        </div>
      </header>

      <main className="app-main">
        <div className="control-panel">
          <button
            className={`record-button ${isRecording ? 'recording' : ''}`}
            onClick={handleToggleRecording}
            disabled={!isConnected}
          >
            {isRecording ? '⏹️ Stop' : '🎤 Start Conversation'}
          </button>
        </div>

        {transcript && (
          <div className="transcript-panel">
            <h3>Assistant Response</h3>
            <p>{transcript}</p>
          </div>
        )}

        {groundingFiles.length > 0 && (
          <div className="citations-panel">
            <h3>📚 Sources</h3>
            <div className="citations-list">
              {groundingFiles.map((file, idx) => (
                <div key={idx} className="citation-card">
                  <h4>{file.title || `Source ${idx + 1}`}</h4>
                  <p className="citation-text">{file.chunk}</p>
                  {file.chunk_id && <small>ID: {file.chunk_id}</small>}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="debug-toggle">
          <button onClick={() => setShowDebug(!showDebug)}>
            {showDebug ? '🔽 Hide Debug' : '🔼 Show Debug'}
          </button>
        </div>

        {showDebug && (
          <div className="debug-panel">
            <h3>Debug Log</h3>
            <div className="debug-content">
              {debugLogs.map((log, idx) => (
                <div key={idx} className="debug-line">{log}</div>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Powered by Azure OpenAI GPT Realtime API & Azure AI Search</p>
      </footer>
    </div>
  );
}

export default App;
