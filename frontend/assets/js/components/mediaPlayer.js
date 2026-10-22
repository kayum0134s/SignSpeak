/**
 * Media Player Component
 * Controls visual presentation for both Gallery Mode (grid layout)
 * and Video Mode (continuous sequential playback with speed regulation).
 */

import { MediaGenerator } from './mediaGenerator.js';
import { CONFIG } from '../utils/config.js';

export class MediaPlayer {
    constructor() {
        this.mediaGenerator = new MediaGenerator();
        this.currentMode = CONFIG.DEFAULT_MODE;
        this.playbackSpeed = CONFIG.DEFAULT_SPEED;
        this.playlist = [];
        this.currentIndex = 0;
        this.imageTimer = null;
        this.isPlaying = false;
    }

    /**
     * Bind DOM elements to media player
     */
    init(elements) {
        this.galleryGrid = elements.galleryGrid;
        this.videoPlayer = elements.videoPlayer;
        this.galleryView = elements.galleryView;
        this.videoView = elements.videoView;
        this.outputDisplay = elements.outputDisplay;

        // Ensure video is configured properly
        if (this.videoPlayer) {
            this.videoPlayer.playbackRate = this.playbackSpeed;
            this.videoPlayer.addEventListener('ended', () => this.handleMediaEnded());
            this.videoPlayer.addEventListener('error', (e) => this.handleMediaError(e));
        }
    }

    /**
     * Set display mode ('gallery' or 'video')
     */
    setMode(mode) {
        if (mode === 'gallery' || mode === 'video') {
            this.currentMode = mode;
        }
    }

    /**
     * Set video playback rate
     */
    setSpeed(speed) {
        this.playbackSpeed = parseFloat(speed) || 1.0;
        if (this.videoPlayer) {
            this.videoPlayer.playbackRate = this.playbackSpeed;
        }
    }

    /**
     * Display translated signs in the active mode
     * @param {Array<object>} signs
     * @param {string} mode - Optional override
     */
    displaySigns(signs, mode = null) {
        const activeMode = mode || this.currentMode;
        this.playlist = signs || [];
        this.currentIndex = 0;

        if (!this.playlist.length) {
            this.showEmptyState();
            return;
        }

        if (activeMode === 'gallery') {
            this.displayGallery(this.playlist);
        } else {
            this.playVideoSequence(this.playlist);
        }
    }

    /**
     * Render Gallery Grid of sign cards
     */
    displayGallery(signs) {
        this.stopCurrentPlayback();

        if (this.outputDisplay) this.outputDisplay.classList.add('hidden');
        if (this.videoView) this.videoView.classList.add('hidden');
        if (this.galleryView) this.galleryView.classList.remove('hidden');

        if (!this.galleryGrid) return;
        this.galleryGrid.innerHTML = '';

        signs.forEach((sign, idx) => {
            const card = document.createElement('div');
            card.className = 'sign-card';
            card.setAttribute('data-index', idx);

            const badge = document.createElement('span');
            badge.className = `card-badge badge-${sign.tokenType || 'sign'}`;
            badge.textContent = sign.tokenType ? sign.tokenType.toUpperCase() : 'SIGN';
            card.appendChild(badge);

            if (sign.type === 'video') {
                const video = document.createElement('video');
                video.className = 'sign-card-video';
                video.src = sign.path;
                video.muted = true;
                video.loop = true;
                video.autoplay = true;
                video.playsInline = true;
                card.appendChild(video);
            } else {
                const img = this.mediaGenerator.createImageWithFallback(
                    sign.path,
                    sign.label || 'Sign',
                    sign.language || 'asl'
                );
                card.appendChild(img);
            }

            const label = document.createElement('div');
            label.className = 'sign-card-label';
            label.textContent = sign.label || 'Sign';
            card.appendChild(label);

            this.galleryGrid.appendChild(card);
        });
    }

    /**
     * Start continuous sequential playback in Video Mode
     */
    playVideoSequence(signs) {
        this.stopCurrentPlayback();

        if (this.outputDisplay) this.outputDisplay.classList.add('hidden');
        if (this.galleryView) this.galleryView.classList.add('hidden');
        if (this.videoView) this.videoView.classList.remove('hidden');

        this.playlist = signs;
        this.currentIndex = 0;
        this.isPlaying = true;

        this.playNext();
    }

    /**
     * Play the next item in the playlist
     */
    playNext() {
        if (!this.isPlaying || this.currentIndex >= this.playlist.length) {
            this.isPlaying = false;
            return;
        }

        const currentSign = this.playlist[this.currentIndex];

        if (currentSign.type === 'video') {
            this.playVideoItem(currentSign);
        } else {
            this.playImageItem(currentSign);
        }
    }

    playVideoItem(sign) {
        if (!this.videoPlayer) return;

        this.videoPlayer.src = sign.path;
        this.videoPlayer.playbackRate = this.playbackSpeed;

        this.videoPlayer.play().catch(err => {
            console.warn(`Video play error for ${sign.path}:`, err);
            // Advance to next after short timeout on autoplay prevention or load fail
            setTimeout(() => this.handleMediaEnded(), 1200);
        });
    }

    playImageItem(sign) {
        if (!this.videoPlayer) return;

        // For images during video mode, load into poster and pause
        this.videoPlayer.src = '';
        this.videoPlayer.poster = sign.path;

        // Image display duration adjusted by playback speed
        const displayTime = Math.max(500, 1500 / this.playbackSpeed);

        this.imageTimer = setTimeout(() => {
            this.handleMediaEnded();
        }, displayTime);
    }

    handleMediaEnded() {
        this.currentIndex++;
        if (this.currentIndex < this.playlist.length) {
            this.playNext();
        } else {
            this.isPlaying = false;
        }
    }

    handleMediaError(e) {
        console.warn('Media element reported error, skipping to next sign:', e);
        setTimeout(() => this.handleMediaEnded(), 500);
    }

    stopCurrentPlayback() {
        this.isPlaying = false;
        if (this.imageTimer) {
            clearTimeout(this.imageTimer);
            this.imageTimer = null;
        }
        if (this.videoPlayer) {
            this.videoPlayer.pause();
            this.videoPlayer.currentTime = 0;
        }
    }

    play() {
        if (this.videoPlayer && this.videoPlayer.src) {
            this.isPlaying = true;
            this.videoPlayer.play();
        } else if (this.playlist.length) {
            this.playVideoSequence(this.playlist);
        }
    }

    pause() {
        this.isPlaying = false;
        if (this.imageTimer) {
            clearTimeout(this.imageTimer);
        }
        if (this.videoPlayer) {
            this.videoPlayer.pause();
        }
    }

    showEmptyState() {
        this.stopCurrentPlayback();
        if (this.galleryView) this.galleryView.classList.add('hidden');
        if (this.videoView) this.videoView.classList.add('hidden');
        if (this.outputDisplay) this.outputDisplay.classList.remove('hidden');
    }

    clear() {
        this.stopCurrentPlayback();
        this.playlist = [];
        this.currentIndex = 0;
        if (this.galleryGrid) this.galleryGrid.innerHTML = '';
        if (this.videoPlayer) {
            this.videoPlayer.src = '';
            this.videoPlayer.poster = '';
        }
        this.showEmptyState();
    }
}

export default MediaPlayer;
