# VoiceRAG Frontend

React + TypeScript + Vite frontend for the VoiceRAG application.

## Features

- 🎤 Real-time voice recording and audio streaming
- 🔊 Audio playback of AI responses
- 📝 Live transcript display
- 📚 Citation/source display from RAG
- 🐛 Debug panel for WebSocket messages and function calls
- 🎨 Modern, responsive UI

## Setup

### Install Dependencies

```bash
npm install
```

### Development

Run the development server with hot reload:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

Build the frontend and output to the backend's wwwroot folder:

```bash
npm run build
```

The built files will be placed in `../backend/wwwroot` and can be served by the C# backend.

## Architecture

### Key Components

- **App.tsx** - Main application component with state management
- **useWebSocket.ts** - Custom hook for WebSocket connection to `/realtime`
- **useAudioRecorder.ts** - Custom hook for microphone capture and PCM16 encoding
- **useAudioPlayer.ts** - Custom hook for decoding and playing audio responses

### Audio Processing

1. **Recording**: Captures microphone input at 24kHz, converts to PCM16, encodes to base64
2. **Streaming**: Sends audio chunks via WebSocket as `input_audio_buffer.append` messages
3. **Playback**: Receives `response.audio.delta` messages, decodes base64 PCM16, plays through Web Audio API

### WebSocket Protocol

Connects to backend at `/realtime` and handles these message types:

- `session.created` - Initialize session with turn detection
- `response.audio.delta` - Audio response chunks
- `response.audio_transcript.delta` - Text transcript of response
- `input_audio_buffer.speech_started` - User started speaking
- `extension.middle_tier_tool_response` - Tool call results (RAG citations, custom tools)
- `error` - Error messages

## Configuration

### Vite Config

- **Dev server**: Port 3000 with WebSocket proxy to backend (localhost:8765)
- **Build output**: `../backend/wwwroot` for integrated deployment

### WebSocket URL

Automatically connects to `ws://${window.location.host}/realtime` which proxies to the backend.

## UI Features

### Main Controls

- **Start/Stop Recording Button** - Toggle voice input
- **Connection Status** - Shows WebSocket connection state

### Display Panels

- **Transcript Panel** - Shows AI assistant's response text
- **Citations Panel** - Displays sources from RAG queries
- **Debug Panel** - Collapsible log of WebSocket events and function calls

## Browser Requirements

- Modern browser with Web Audio API support
- Microphone permissions
- WebSocket support

## Development Tips

### Testing Audio

1. Start the backend: `cd ../backend && dotnet run`
2. Start the frontend: `npm run dev`
3. Click "Start Conversation" and allow microphone access
4. Speak a query about the indexed documents

### Debugging

- Enable the debug panel to see all WebSocket messages
- Check browser console for audio processing errors
- Verify WebSocket connection in Network tab

## Customization

### Styling

Edit `App.css` to customize colors, layouts, and animations.

### Audio Format

Default: 24kHz PCM16. To change, update sample rate in:
- `useAudioRecorder.ts` (AudioContext)
- `useAudioPlayer.ts` (AudioContext and buffer creation)

### WebSocket Messages

Add custom message handlers in `App.tsx` under the `useEffect` that processes `lastMessage`.

## Troubleshooting

### WebSocket Connection Failed

- Ensure backend is running on port 8765
- Check CORS settings in backend
- Verify `/realtime` endpoint is available

### No Audio Playback

- Check browser console for audio errors
- Ensure audio autoplay is allowed
- Try clicking a button before audio playback (browser autoplay policy)

### Microphone Access Denied

- Grant microphone permissions in browser settings
- Use HTTPS in production (required for mic access)

## License

MIT
