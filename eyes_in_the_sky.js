const Max = require('max-api');
const http = require('http');

// We use lightweight HTTP to ping the Python backend
let aiListening = false;
let currentBpm = 120.0;
let isPlaying = false;

// 1. Listen for the ON/OFF toggle from your Ableton panel
Max.addHandler('toggle_listen', (state) => {
    aiListening = (state === 1);
    Max.post(`AI Listening Mode: ${aiListening ? 'ON' : 'OFF'}`);
});

// 2. The Watchtower: Receives live BPM and Transport data from Ableton
Max.addHandler('telemetry', (bpm, playing_state) => {
    currentBpm = bpm;
    isPlaying = (playing_state === 1);
    
    // Only send data to the Swarm if the AI is told to listen
    if (aiListening) {
        sendToSwarm({
            event: "status_update",
            bpm: currentBpm,
            playing: isPlaying,
            timestamp: Date.now()
        });
    }
});

// 3. The Transmission Engine: Shoots data to your local Python hub
function sendToSwarm(payload) {
    const data = JSON.stringify(payload);
    const options = {
        hostname: 'localhost',
        port: 8000, // FastAPI gateway port
        path: '/ableton-telemetry',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': data.length
        }
    };
    
    const req = http.request(options, (res) => {
        // AI received it silently
    });
    
    req.on('error', (error) => {
        Max.post(`Swarm disconnected: ${error.message}`);
    });
    
    req.write(data);
    req.end();
}

Max.post("Eyes in the Sky: ONLINE. Awaiting Swarm Link.");
