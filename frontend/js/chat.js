/**
 * Curelink Disha - Chat Manager
 */

const Chat = {
    messagesContainer: null,
    input: null,
    sendButton: null,
    voiceButton: null,
    typingIndicator: null,
    userId: null,
    isSending: false,
    isRecording: false,
    recognition: null,
    lastMessageDate: null,

    /**
     * Initialize chat
     */
    init() {
        this.messagesContainer = document.getElementById('messages-container');
        this.input = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.voiceButton = document.getElementById('voice-button');
        this.typingIndicator = document.getElementById('typing-indicator');

        this.setupInputHandlers();
        this.setupVoiceHandlers();
        this.autoResizeInput();
    },

    /**
     * Setup input event handlers
     */
    setupInputHandlers() {
        // Input change handler
        this.input.addEventListener('input', () => {
            this.handleInputChange();
            this.autoResizeInput();
        });

        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Enter key to send (Shift+Enter for new line)
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Focus input on page load
        this.input.focus();
    },

    /**
     * Setup voice handlers
     */
    setupVoiceHandlers() {
        if (!this.voiceButton) return;

        // Check for browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            this.voiceButton.style.display = 'none';
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-IN'; // Set to Indian English for better accuracy with accents/Hinglish

        this.voiceButton.addEventListener('click', () => {
            if (this.isRecording) {
                this.stopRecording();
            } else {
                this.startRecording();
            }
        });

        this.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0])
                .map(result => result.transcript)
                .join('');

            this.input.value = transcript;
            this.handleInputChange();
            this.autoResizeInput();
        };

        this.recognition.onend = () => {
            this.stopRecording();
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.stopRecording();
            Utils.showToast('Voice input error: ' + event.error, 'error');
        };
    },

    startRecording() {
        if (this.isRecording) return;
        
        try {
            this.recognition.start();
            this.isRecording = true;
            this.voiceButton.classList.add('recording');
            this.input.placeholder = 'Listening...';
        } catch (error) {
            console.error('Speech recognition failed to start:', error);
        }
    },

    stopRecording() {
        if (!this.isRecording) return;
        
        this.recognition.stop();
        this.isRecording = false;
        this.voiceButton.classList.remove('recording');
        this.input.placeholder = 'Type a message...';
    },

    /**
     * Handle input change
     */
    handleInputChange() {
        const hasContent = this.input.value.trim().length > 0;
        this.sendButton.disabled = !hasContent || this.isSending;
    },

    /**
     * Auto-resize textarea
     */
    autoResizeInput() {
        this.input.style.height = 'auto';
        this.input.style.height = Math.min(this.input.scrollHeight, 120) + 'px';
    },

    /**
     * Send a message
     */
    async sendMessage(text = null) {
        const content = text || this.input.value.trim();

        if (!content || this.isSending) return;

        this.isSending = true;
        this.sendButton.disabled = true;
        this.sendButton.classList.add('sending');

        // Optimistic UI: Add user message immediately
        const tempUserMsg = {
            id: 'temp-' + Date.now(),
            role: 'user',
            content: content,
            timestamp: new Date().toISOString()
        };
        this.addMessage(tempUserMsg);
        ScrollManager.scrollToBottom();

        // Clear input immediately if it came from the textarea
        if (!text) {
            this.input.value = '';
            this.autoResizeInput();
        }

        // Show typing indicator
        this.showTyping(true);

        try {
            const response = await API.sendMessage(this.userId, content);

            // Hide typing
            this.showTyping(false);

            // Add assistant message (which might have options)
            if (response.assistant_message) {
                this.addMessage(response.assistant_message);
            }

            // Scroll to bottom
            ScrollManager.scrollToBottom();

        } catch (error) {
            console.error('Send message error:', error);
            Utils.showToast(error.message || 'Failed to send message', 'error');

            // Find the temp message and mark it as failed
            const tempMsgElement = document.querySelector(`[data-message-id="${tempUserMsg.id}"]`);
            if (tempMsgElement) {
                tempMsgElement.classList.add('failed');
            }

            this.showTyping(false);
        } finally {
            this.isSending = false;
            this.handleInputChange();
            this.sendButton.classList.remove('sending');
            this.input.focus();
        }
    },

    /**
     * Add a message to the chat
     */
    addMessage(message, prepend = false) {
        // If it's a real user message and we have a temp one, don't re-add it
        // Our Optimistic UI handles the user message display
        if (message.role === 'user' && !message.id.startsWith('temp-')) {
            const existing = document.querySelector(`[data-message-id^="temp-"]`);
            if (existing && existing.querySelector('.message-content').textContent === message.content) {
                existing.dataset.messageId = message.id;
                existing.classList.remove('optimistic');
                return;
            }
        }

        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${message.role}`;
        if (message.id.startsWith('temp-')) wrapper.classList.add('optimistic');
        wrapper.dataset.messageId = message.id;

        // Check if we need a date divider
        const messageDate = new Date(message.timestamp).toDateString();
        if (!prepend && this.lastMessageDate !== messageDate) {
            if (this.lastMessageDate !== null) {
                const divider = this.createDateDivider(message.timestamp);
                this.messagesContainer.appendChild(divider);
            }
            this.lastMessageDate = messageDate;
        }

        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${message.role}`;

        const content = document.createElement('div');
        content.className = 'message-content';

        // Check if emoji only
        if (Utils.isEmojiOnly(message.content)) {
            content.classList.add('emoji-only');
            content.textContent = message.content;
        } else {
            content.innerHTML = Utils.parseFormatting(message.content);
        }

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = Utils.formatTime(message.timestamp);

        bubble.appendChild(content);
        bubble.appendChild(time);
        wrapper.appendChild(bubble);

        // Add options if any
        if (message.options && message.options.length > 0) {
            const optionsContainer = this.renderOptions(message.options);
            wrapper.appendChild(optionsContainer);
        }

        if (prepend) {
            this.messagesContainer.insertBefore(wrapper, this.messagesContainer.firstChild);
        } else {
            this.messagesContainer.appendChild(wrapper);

            // If it's the latest message and from assistant, wait a bit then scroll
            if (message.role === 'assistant') {
                setTimeout(() => ScrollManager.scrollToBottom(), 50);
            }
        }
    },

    /**
     * Render quick reply options (CTAs)
     */
    renderOptions(options) {
        const container = document.createElement('div');
        container.className = 'message-options';

        options.forEach(option => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.textContent = option;
            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                // When clicked, send this as a message
                this.sendMessage(option);
                // Hide all options in this container after one is clicked
                container.style.display = 'none';
            };
            container.appendChild(btn);
        });

        return container;
    },

    /**
     * Prepend messages (for loading older)
     */
    prependMessages(messages) {
        // Sort messages by timestamp (oldest first)
        const sorted = [...messages].sort((a, b) =>
            new Date(a.timestamp) - new Date(b.timestamp)
        );

        // Track dates for dividers
        let lastDate = null;
        const fragment = document.createDocumentFragment();

        sorted.forEach(message => {
            const messageDate = new Date(message.timestamp).toDateString();

            if (lastDate !== messageDate) {
                const divider = this.createDateDivider(message.timestamp);
                fragment.appendChild(divider);
                lastDate = messageDate;
            }

            const wrapper = document.createElement('div');
            wrapper.className = `message-wrapper ${message.role}`;
            wrapper.dataset.messageId = message.id;

            const bubble = document.createElement('div');
            bubble.className = `message-bubble ${message.role}`;

            const content = document.createElement('div');
            content.className = 'message-content';

            if (Utils.isEmojiOnly(message.content)) {
                content.classList.add('emoji-only');
                content.textContent = message.content;
            } else {
                content.innerHTML = Utils.parseFormatting(message.content);
            }

            const time = document.createElement('div');
            time.className = 'message-time';
            time.textContent = Utils.formatTime(message.timestamp);

            bubble.appendChild(content);
            bubble.appendChild(time);
            wrapper.appendChild(bubble);
            fragment.appendChild(wrapper);
        });

        // Insert at beginning
        if (this.messagesContainer.firstChild) {
            this.messagesContainer.insertBefore(fragment, this.messagesContainer.firstChild);
        } else {
            this.messagesContainer.appendChild(fragment);
        }
    },

    /**
     * Create date divider
     */
    createDateDivider(timestamp) {
        const divider = document.createElement('div');
        divider.className = 'date-divider';

        const span = document.createElement('span');
        span.textContent = Utils.formatDate(timestamp);

        divider.appendChild(span);
        return divider;
    },

    /**
     * Load initial messages
     */
    async loadMessages() {
        try {
            const response = await API.getLatestMessages(this.userId, 50);

            if (response.messages && response.messages.length > 0) {
                // Clear container
                this.messagesContainer.innerHTML = '';
                this.lastMessageDate = null;

                // Add messages
                response.messages.forEach(message => this.addMessage(message));

                // Setup scroll manager
                ScrollManager.setHasMore(response.has_more);
                if (response.messages.length > 0) {
                    ScrollManager.setOldestMessageId(response.messages[0].id);
                }

                // Scroll to bottom
                ScrollManager.scrollToBottom(false);
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            Utils.showToast('Failed to load messages', 'error');
        }
    },

    /**
     * Show/hide typing indicator
     */
    showTyping(show) {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = show ? 'block' : 'none';

            // Update status text
            const statusText = document.getElementById('status-text');
            if (statusText) {
                statusText.textContent = show ? 'typing...' : 'Your AI Health Coach';
                document.body.classList.toggle('status-typing', show);
            }

            if (show) {
                ScrollManager.scrollToBottom();
            }
        }
    },

    /**
     * Set user ID
     */
    setUserId(userId) {
        this.userId = userId;
    },

    /**
     * Clear chat
     */
    clear() {
        this.messagesContainer.innerHTML = '';
        this.lastMessageDate = null;
        ScrollManager.reset();
    }
};

// Make Chat available globally
window.Chat = Chat;
