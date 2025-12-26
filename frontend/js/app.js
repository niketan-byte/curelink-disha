/**
 * Curelink Disha - Main Application
 */

const App = {
    userId: null,
    isInitialized: false,

    /**
     * Initialize the application
     */
    async init() {
        console.log('🚀 Initializing Disha Health Coach...');

        try {
            // Initialize components
            Chat.init();
            ScrollManager.init('chat-container');

            // Check for existing user session
            this.userId = Utils.storage.get('userId');

            if (this.userId) {
                // Validate existing user
                try {
                    await API.getUser(this.userId);
                    console.log('✓ Existing user session found:', this.userId);
                } catch (error) {
                    console.log('⚠ User session invalid, creating new...');
                    this.userId = null;
                    Utils.storage.remove('userId');
                }
            }

            if (!this.userId) {
                // Create new user
                await this.createNewUser();
            }

            // Set user ID in chat
            Chat.setUserId(this.userId);

            // Initialize WebSocket
            WS.init(this.userId);

            // Load existing messages
            await Chat.loadMessages();

            // Check if this is a new user (no messages)
            const messagesContainer = document.getElementById('messages-container');
            if (messagesContainer && messagesContainer.children.length === 0) {
                // Trigger initial greeting by sending empty "start" message
                await this.triggerInitialGreeting();
            }

            // Hide loading screen
            this.hideLoadingScreen();

            this.isInitialized = true;
            console.log('✓ App initialized successfully');

        } catch (error) {
            console.error('❌ App initialization failed:', error);
            this.showError('Failed to initialize. Please refresh the page.');
        }
    },

    /**
     * Create a new user session
     */
    async createNewUser() {
        try {
            const response = await API.createUser();
            this.userId = response.user_id;
            Utils.storage.set('userId', this.userId);
            console.log('✓ New user created:', this.userId);
        } catch (error) {
            console.error('Failed to create user:', error);
            throw error;
        }
    },

    /**
     * Trigger initial greeting from the bot
     */
    async triggerInitialGreeting() {
        // Show typing indicator
        Chat.showTyping(true);

        try {
            // Send a "start" message to trigger onboarding
            const response = await API.sendMessage(this.userId, 'hi');

            Chat.showTyping(false);

            // Add the assistant's greeting
            if (response.assistant_message) {
                Chat.addMessage(response.assistant_message);
                ScrollManager.scrollToBottom(false);
            }
        } catch (error) {
            console.error('Failed to get initial greeting:', error);
            Chat.showTyping(false);

            // Show a default greeting on error
            Chat.addMessage({
                id: 'welcome-1',
                role: 'assistant',
                content: "Hey there! 👋 I'm Disha, your personal health coach from Curelink. I'm here to help you with your health and wellness journey!\n\nBefore we start, I'd love to know a bit about you. What should I call you?",
                timestamp: new Date().toISOString()
            });
        }
    },

    /**
     * Hide loading screen
     */
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 400);
        }
    },

    /**
     * Show error message
     */
    showError(message) {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.innerHTML = `
                <div class="loading-content">
                    <h2>Oops!</h2>
                    <p style="color: rgba(255,255,255,0.9);">${message}</p>
                    <button onclick="location.reload()" style="
                        margin-top: 20px;
                        padding: 12px 24px;
                        background: white;
                        color: #128C7E;
                        border: none;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                    ">Refresh Page</button>
                </div>
            `;
        }
    },

    /**
     * Reset and start new chat
     */
    async resetChat() {
        Utils.storage.remove('userId');
        location.reload();
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

// Make App available globally
window.App = App;
