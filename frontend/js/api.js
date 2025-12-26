/**
 * Curelink Disha - API Client
 */

const API = {
    // Base URL - change this for production
    baseUrl: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'
        : 'https://curelink-disha.onrender.com',

    /**
     * Set the base URL (for production)
     */
    setBaseUrl(url) {
        this.baseUrl = url;
    },

    /**
     * Make an API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);

            // Handle rate limiting
            if (response.status === 429) {
                throw new Error('Too many messages. Please slow down and try again in a minute.');
            }

            // Handle server errors
            if (response.status >= 500) {
                throw new Error('Server error. Please try again later.');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'An error occurred');
            }

            return data;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Unable to connect to server. Please check your connection.');
            }
            throw error;
        }
    },

    /**
     * Create a new user session
     */
    async createUser() {
        return this.request('/api/users', {
            method: 'POST',
            body: JSON.stringify({}),
        });
    },

    /**
     * Get user by ID
     */
    async getUser(userId) {
        return this.request(`/api/users/${userId}`);
    },

    /**
     * Send a message and get AI response
     */
    async sendMessage(userId, content) {
        return this.request('/api/messages', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                content: content,
            }),
        });
    },

    /**
     * Get message history (paginated)
     */
    async getMessages(userId, beforeId = null, limit = 20) {
        let endpoint = `/api/messages?user_id=${userId}&limit=${limit}`;
        if (beforeId) {
            endpoint += `&before=${beforeId}`;
        }
        return this.request(endpoint);
    },

    /**
     * Get latest messages (for initial load)
     */
    async getLatestMessages(userId, limit = 50) {
        return this.request(`/api/messages/latest?user_id=${userId}&limit=${limit}`);
    },

    /**
     * Health check
     */
    async healthCheck() {
        return this.request('/health');
    }
};

// Make API available globally
window.API = API;
