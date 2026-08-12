const WebSocket = require('ws');
const http = require('http');

const PORT = process.env.PORT || 10000;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('LingoLens Live Proxy Server Running');
});

const wss = new WebSocket.Server({ server });

wss.on('connection', (clientWs) => {
    console.log('[Proxy] Client connected');

    if (!GEMINI_API_KEY) {
        console.error('[Proxy Error] GEMINI_API_KEY is not set');
        clientWs.close();
        return;
    }

    const geminiUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${GEMINI_API_KEY}`;
    const geminiWs = new WebSocket(geminiUrl);

    geminiWs.on('open', () => {
        console.log('[Proxy] Connected to Gemini Live API');
    });

    geminiWs.on('message', (data) => {
        if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(data.toString());
        }
    });

    clientWs.on('message', (message) => {
        if (geminiWs.readyState === WebSocket.OPEN) {
            geminiWs.send(message.toString());
        }
    });

    clientWs.on('close', () => {
        console.log('[Proxy] Client disconnected');
        if (geminiWs.readyState === WebSocket.OPEN) geminiWs.close();
    });

    geminiWs.on('close', () => {
        console.log('[Proxy] Gemini disconnected');
        if (clientWs.readyState === WebSocket.OPEN) clientWs.close();
    });

    geminiWs.on('error', (err) => {
        console.error('[Proxy Gemini Error]:', err);
    });

    clientWs.on('error', (err) => {
        console.error('[Proxy Client Error]:', err);
    });
});

server.listen(PORT, () => {
    console.log(`[Proxy] Server listening on port ${PORT}`);
});
