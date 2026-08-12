const WebSocket = require('ws');
const http = require('http');

const PORT = process.env.PORT || 8080;
// ჩასვით თქვენი AIzaSy... კოდი ბრჭყალებში
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "AIzaSy...თქვენი_კოდი_აქ...";

if (!GEMINI_API_KEY) {
    console.error("ERROR: GEMINI_API_KEY არ არის მითითებული!");
    process.exit(1);
}

const server = http.createServer();
const wss = new WebSocket.Server({ server });

wss.on('connection', (clientWs) => {
    console.log('[Proxy]: LingoLens კლიენტი დაუკავშირდა.');

    const geminiUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${GEMINI_API_KEY}`;
    const geminiWs = new WebSocket(geminiUrl);

    geminiWs.on('open', () => {
        console.log('[Proxy]: Gemini Live API კავშირი დამყარდა.');
    });

    clientWs.on('message', (message) => {
        if (geminiWs.readyState === WebSocket.OPEN) {
            geminiWs.send(message);
        }
    });

    geminiWs.on('message', (data) => {
        if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(data);
        }
    });

    clientWs.on('close', () => geminiWs.close());
    geminiWs.on('close', () => clientWs.close());
    clientWs.on('error', (err) => console.error('[Client Error]:', err));
    geminiWs.on('error', (err) => console.error('[Gemini Error]:', err));
});

server.listen(PORT, () => {
    console.log(`LingoLens Proxy Server გაშვიებულია პორტზე: ${PORT}`);
});
