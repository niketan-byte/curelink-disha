/**
 * Curelink Disha - Scroll Manager
 */

const ScrollManager = {
    container: null,
    isLoadingMore: false,
    hasMoreMessages: true,
    oldestMessageId: null,

    /**
     * Initialize scroll manager
     */
    init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Scroll container not found');
            return;
        }

        this.setupScrollListener();
    },

    /**
     * Setup scroll event listener for infinite scroll
     */
    setupScrollListener() {
        const throttledScroll = Utils.throttle(() => {
            this.handleScroll();
        }, 200);

        this.container.addEventListener('scroll', throttledScroll);
    },

    /**
     * Handle scroll event
     */
    handleScroll() {
        // Check if scrolled near top (for loading older messages)
        if (this.container.scrollTop < 100 && !this.isLoadingMore && this.hasMoreMessages) {
            this.loadOlderMessages();
        }
    },

    /**
     * Load older messages
     */
    async loadOlderMessages() {
        if (this.isLoadingMore || !this.hasMoreMessages || !this.oldestMessageId) {
            return;
        }

        this.isLoadingMore = true;
        this.showLoadingIndicator(true);

        try {
            const userId = Utils.storage.get('userId');
            if (!userId) return;

            // Remember scroll position
            const scrollHeight = this.container.scrollHeight;
            const scrollTop = this.container.scrollTop;

            const response = await API.getMessages(userId, this.oldestMessageId, 20);

            if (response.messages && response.messages.length > 0) {
                // Update oldest message ID
                this.oldestMessageId = response.next_cursor || response.messages[0].id;
                this.hasMoreMessages = response.has_more;

                // Prepend messages
                Chat.prependMessages(response.messages);

                // Maintain scroll position
                const newScrollHeight = this.container.scrollHeight;
                this.container.scrollTop = scrollTop + (newScrollHeight - scrollHeight);
            } else {
                this.hasMoreMessages = false;
            }
        } catch (error) {
            console.error('Error loading older messages:', error);
            Utils.showToast('Failed to load older messages', 'error');
        } finally {
            this.isLoadingMore = false;
            this.showLoadingIndicator(false);
        }
    },

    /**
     * Show/hide loading indicator
     */
    showLoadingIndicator(show) {
        const indicator = document.getElementById('load-more-indicator');
        if (indicator) {
            indicator.style.display = show ? 'flex' : 'none';
        }
    },

    /**
     * Scroll to bottom of chat
     */
    scrollToBottom(smooth = true) {
        if (!this.container) return;

        requestAnimationFrame(() => {
            this.container.scrollTo({
                top: this.container.scrollHeight,
                behavior: smooth ? 'smooth' : 'auto'
            });
        });
    },

    /**
     * Check if scrolled to bottom
     */
    isAtBottom() {
        if (!this.container) return true;

        const threshold = 100;
        return (this.container.scrollHeight - this.container.scrollTop - this.container.clientHeight) < threshold;
    },

    /**
     * Set oldest message ID for pagination
     */
    setOldestMessageId(id) {
        this.oldestMessageId = id;
    },

    /**
     * Set has more messages flag
     */
    setHasMore(hasMore) {
        this.hasMoreMessages = hasMore;
    },

    /**
     * Reset scroll state
     */
    reset() {
        this.isLoadingMore = false;
        this.hasMoreMessages = true;
        this.oldestMessageId = null;
    }
};

// Make ScrollManager available globally
window.ScrollManager = ScrollManager;
