/**
 * Media Player Module
 * Handles display and playback of sign language media (images/videos)
 */

class MediaPlayer {
    constructor() {
        this.currentMode = 'video'; // Default to video mode
        this.signs = [];
        this.currentIndex = 0;

        // DOM elements (will be initialized by app)
        this.galleryGrid = null;
        this.videoPlayer = null;
        this.galleryView = null;
        this.videoView = null;
        this.outputDisplay = null;
    }

    /**
     * Initialize with DOM elements
     */
    init(elements) {
        this.galleryGrid = elements.galleryGrid;
        this.videoPlayer = elements.videoPlayer;
        this.galleryView = elements.galleryView;
        this.videoView = elements.videoView;
        this.outputDisplay = elements.outputDisplay;
    }

    /**
     * Set display mode
     * @param {string} mode - 'gallery' or 'video'
     */
    setMode(mode) {
        this.currentMode = mode;
        this.updateDisplay();
    }

    /**
     * Load and display signs
     * @param {array} signs - Array of sign objects from translator
     */
    async displaySigns(signs) {
        this.signs = signs;
        this.currentIndex = 0;

        if (signs.length === 0) {
            this.showPlaceholder();
            return;
        }

        // Hide placeholder
        if (this.outputDisplay) {
            this.outputDisplay.classList.add('hidden');
        }

        if (this.currentMode === 'gallery') {
            await this.displayGallery();
        } else {
            await this.displayVideo();
        }
    }

    /**
     * Display signs in gallery mode
     */
    async displayGallery() {
        if (!this.galleryGrid || !this.galleryView) return;

        // Clear existing content
        this.galleryGrid.innerHTML = '';

        // Show gallery view
        this.galleryView.classList.remove('hidden');
        this.videoView.classList.add('hidden');

        // Create sign cards
        for (const sign of this.signs) {
            const card = this.createSignCard(sign);
            this.galleryGrid.appendChild(card);
        }
    }

    /**
     * Create a sign card element
     * @param {object} sign
     * @returns {HTMLElement}
     */
    createSignCard(sign) {
        const card = document.createElement('div');
        card.className = 'sign-card';

        // Check if it's a video or image
        if (sign.type === 'video' && !sign.path.startsWith('data:')) {
            // Create video element for real video files
            const video = document.createElement('video');
            video.className = 'sign-image';
            video.src = sign.path;
            video.alt = sign.label;
            video.controls = true;
            video.loop = true;
            video.muted = true; // Autoplay requires muted

            // Handle video load errors
            video.onerror = () => {
                video.style.display = 'none';
                const placeholder = document.createElement('div');
                placeholder.style.cssText = `
                    width: 100%;
                    height: 150px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(102, 126, 234, 0.1);
                    border-radius: 8px;
                    font-size: 3rem;
                `;
                placeholder.textContent = '🎬';
                card.insertBefore(placeholder, card.firstChild);
            };

            card.appendChild(video);
        } else {
            // Create image element
            const img = document.createElement('img');
            img.className = 'sign-image';
            img.alt = sign.label;
            img.src = sign.path;

            // Handle image load errors - create placeholder
            img.onerror = () => {
                img.style.display = 'none';
                const placeholder = document.createElement('div');
                placeholder.style.cssText = `
                    width: 100%;
                    height: 150px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(102, 126, 234, 0.1);
                    border-radius: 8px;
                    font-size: 3rem;
                `;
                placeholder.textContent = '✋';
                card.insertBefore(placeholder, card.firstChild);
            };

            card.appendChild(img);
        }

        const label = document.createElement('div');
        label.className = 'sign-label';
        label.textContent = sign.label.charAt(0).toUpperCase() + sign.label.slice(1);

        // Add fingerspelling indicator
        if (sign.isFingerSpelling) {
            label.textContent = `${label.textContent} (fingerspelling)`;
        }

        card.appendChild(label);

        return card;
    }

    /**
     * Display signs as video sequence
     */
    async displayVideo() {
        if (!this.videoPlayer || !this.videoView) return;

        // Hide gallery, show video
        this.galleryView.classList.add('hidden');
        this.videoView.classList.remove('hidden');

        // Filter for video signs
        const videoSigns = this.signs.filter(s => s.type === 'video' && !s.path.startsWith('data:'));

        if (videoSigns.length > 0) {
            // Play first video
            this.currentIndex = 0;
            this.loadVideo(videoSigns[this.currentIndex]);

            // Set up event listener to play next video when current ends
            this.videoPlayer.onended = () => {
                this.currentIndex++;
                if (this.currentIndex < videoSigns.length) {
                    this.loadVideo(videoSigns[this.currentIndex]);
                } else {
                    // All videos played, loop back to start
                    this.currentIndex = 0;
                    this.loadVideo(videoSigns[this.currentIndex]);
                }
            };

            // Auto-play the first video
            this.videoPlayer.load();
            setTimeout(() => {
                this.videoPlayer.play().catch(err => {
                    console.log('Autoplay prevented, user must click play:', err);
                });
            }, 100);
        } else {
            // No video signs available, show message
            console.log('No video signs available for playback');
            this.videoPlayer.src = '';
        }
    }

    /**
     * Load a video into the player
     * @param {object} sign 
     */
    loadVideo(sign) {
        if (this.videoPlayer) {
            this.videoPlayer.src = sign.path;
            this.videoPlayer.load();
        }
    }

    /**
     * Show placeholder
     */
    showPlaceholder() {
        if (this.outputDisplay) {
            this.outputDisplay.classList.remove('hidden');
        }
        if (this.galleryView) {
            this.galleryView.classList.add('hidden');
        }
        if (this.videoView) {
            this.videoView.classList.add('hidden');
        }
    }

    /**
     * Update display based on current mode
     */
    updateDisplay() {
        if (this.signs.length > 0) {
            this.displaySigns(this.signs);
        }
    }

    /**
     * Get current signs for download
     * @returns {array}
     */
    getCurrentSigns() {
        return this.signs;
    }

    /**
     * Play video
     */
    play() {
        if (this.videoPlayer && this.currentMode === 'video') {
            this.videoPlayer.play();
        }
    }

    /**
     * Pause video
     */
    pause() {
        if (this.videoPlayer && this.currentMode === 'video') {
            this.videoPlayer.pause();
        }
    }

    /**
     * Set playback speed
     * @param {number} speed
     */
    setSpeed(speed) {
        if (this.videoPlayer) {
            this.videoPlayer.playbackRate = speed;
        }
    }
}

export default MediaPlayer;
