(function () {
    const outputText = document.getElementById('output-text');
    const terminalBody = document.getElementById('terminal-body');
    const statusEl = document.getElementById('status');

    let ws = null;

    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            statusEl.textContent = 'Connected';
            statusEl.classList.add('connected');
        };

        ws.onmessage = (event) => {
            outputText.textContent += event.data;
            terminalBody.scrollTop = terminalBody.scrollHeight;
        };

        ws.onclose = () => {
            statusEl.textContent = 'Disconnected';
            statusEl.classList.remove('connected');
            outputText.textContent += '\r\n[Connection closed by server]\r\n';
            terminalBody.scrollTop = terminalBody.scrollHeight;
        };

        ws.onerror = (err) => {
            console.error('WebSocket error:', err);
        };
    }

    function sendTap() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(' ');
        }
    }

    // Keyboard spacebar handler
    window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' || e.key === ' ') {
            e.preventDefault();
            sendTap();
        }
    });

    // Auto focus terminal area
    terminalBody.addEventListener('click', () => {
        window.focus();
    });

    connect();
})();
