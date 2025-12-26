/**
 * Curelink Disha - WebSocket Client
 */

const WS = {
    socket: null,
    userId: null,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    reconnectAttempts: 0,

    /**
     * Initialize WebSocket connection
     */
    init(userId) {
        this.userId = userId;
        this.connect();
    },

    /**
     * Connect to WebSocket
     */
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = API.baseUrl.replace(/^http:\/\/|^https:\/\//, '') || window.location.host;
        const wsUrl = `${protocol}//${host}/ws/chat/${this.userId}`;

        console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = (event) => {
            console.log('✓ WebSocket connected');
            this.reconnectAttempts = 0;

            // Send ping every 30s to keep connection alive
            this.pingInterval = setInterval(() => {
                if (this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send(JSON.stringify({ event: 'ping' }));
                }
            }, 30000);
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleEvent(data);
            } catch (e) {
                console.error('WebSocket message parsing error:', e);
            }
        };

        this.socket.onclose = (event) => {
            console.log('✖ WebSocket disconnected');
            clearInterval(this.pingInterval);

            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Reconnecting in ${this.reconnectInterval}ms (Attempt ${this.reconnectAttempts})...`);
                setTimeout(() => this.connect(), this.reconnectInterval);
            }
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    },

    /**
     * Handle incoming events
     */
    handleEvent(data) {
        const { event } = data;

        if (event === 'typing_start') {
            Chat.showTyping(true);
        } else if (event === 'typing_end') {
            Chat.showTyping(false);
        }
    },

    /**
     * Close connection
     */
    close() {
        if (this.socket) {
            this.socket.close();
        }
    }
};

// Make WS available globally
window.WS = WS;
