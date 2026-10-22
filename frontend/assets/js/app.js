/**
 * Main Application Orchestrator
 * Coordinates UI inputs, Speech Recognition, API Services, and Media Playback.
 */

import { SpeechRecognitionHandler } from './components/speechRecognition.js';
import { MediaPlayer } from './components/mediaPlayer.js';
import { ApiService } from './services/apiService.js';
import { CONFIG } from './utils/config.js';

class App {
    constructor() {
        this.speechRecognition = new SpeechRecognitionHandler();
        this.apiService = new ApiService();
        this.mediaPlayer = new MediaPlayer();

        this.currentLanguage = CONFIG.DEFAULT_LANGUAGE;
        this.currentMode = CONFIG.DEFAULT_MODE;
        this.isProcessing = false;

        this.init();
    }

    async init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }

    setupUI() {
        // Collect DOM references
        this.elements = {
            textInput: document.getElementById('textInput'),
            micBtn: document.getElementById('micBtn'),
            translateBtn: document.getElementById('translateBtn'),
            clearBtn: document.getElementById('clearBtn'),
            speechStatus: document.getElementById('speechStatus'),
            outputDisplay: document.getElementById('outputDisplay'),
            galleryView: document.getElementById('galleryView'),
            galleryGrid: document.getElementById('galleryGrid'),
            videoView: document.getElementById('videoView'),
            signVideo: document.getElementById('signVideo'),
            playBtn: document.getElementById('playBtn'),
            pauseBtn: document.getElementById('pauseBtn'),
            speedSlider: document.getElementById('speedSlider'),
            speedValue: document.getElementById('speedValue'),
            statusBar: document.getElementById('statusBar'),
            statusText: document.getElementById('statusText'),
            progressFill: document.getElementById('progressFill'),
            currentLanguage: document.getElementById('currentLanguage'),
            languageToggles: document.querySelectorAll('.toggle-btn'),
            modeToggles: document.querySelectorAll('.mode-btn'),
            aboutBtn: document.getElementById('aboutBtn'),
            aboutModal: document.getElementById('aboutModal'),
            modalClose: document.querySelector('.modal-close')
        };

        // Initialize Media Player component
        this.mediaPlayer.init({
            galleryGrid: this.elements.galleryGrid,
            videoPlayer: this.elements.signVideo,
            galleryView: this.elements.galleryView,
            videoView: this.elements.videoView,
            outputDisplay: this.elements.outputDisplay
        });

        this.setupEventListeners();
        this.setupSpeechRecognition();
    }

    setupEventListeners() {
        // Translate Button
        if (this.elements.translateBtn) {
            this.elements.translateBtn.addEventListener('click', () => this.handleTranslate());
        }

        // Clear Button
        if (this.elements.clearBtn) {
            this.elements.clearBtn.addEventListener('click', () => this.handleClear());
        }

        // Microphone Button
        if (this.elements.micBtn) {
            this.elements.micBtn.addEventListener('click', () => this.handleMicClick());
        }

        // Language Selectors
        if (this.elements.languageToggles) {
            this.elements.languageToggles.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const lang = e.currentTarget.dataset.lang;
                    if (lang) this.handleLanguageChange(lang);
                });
            });
        }

        // Mode Selectors
        if (this.elements.modeToggles) {
            this.elements.modeToggles.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const mode = e.currentTarget.dataset.mode;
                    if (mode) this.handleModeChange(mode);
                });
            });
        }

        // Video Controls
        if (this.elements.playBtn) {
            this.elements.playBtn.addEventListener('click', () => this.mediaPlayer.play());
        }
        if (this.elements.pauseBtn) {
            this.elements.pauseBtn.addEventListener('click', () => this.mediaPlayer.pause());
        }
        if (this.elements.speedSlider) {
            this.elements.speedSlider.addEventListener('input', (e) => {
                const speed = e.target.value;
                this.mediaPlayer.setSpeed(speed);
                if (this.elements.speedValue) {
                    this.elements.speedValue.textContent = `${speed}x`;
                }
            });
        }

        // About Modal
        if (this.elements.aboutBtn && this.elements.aboutModal) {
            this.elements.aboutBtn.addEventListener('click', () => {
                this.elements.aboutModal.classList.remove('hidden');
            });
        }
        if (this.elements.modalClose && this.elements.aboutModal) {
            this.elements.modalClose.addEventListener('click', () => {
                this.elements.aboutModal.classList.add('hidden');
            });
        }
        if (this.elements.aboutModal) {
            this.elements.aboutModal.addEventListener('click', (e) => {
                if (e.target === this.elements.aboutModal) {
                    this.elements.aboutModal.classList.add('hidden');
                }
            });
        }

        // Keyboard Shortcut: Enter to translate (Ctrl+Enter or Cmd+Enter)
        if (this.elements.textInput) {
            this.elements.textInput.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    e.preventDefault();
                    this.handleTranslate();
                }
            });
        }
    }

    setupSpeechRecognition() {
        this.speechRecognition.onResult((transcript, isFinal) => {
            if (this.elements.textInput) {
                this.elements.textInput.value = transcript;
            }
            if (isFinal) {
                this.handleTranslate();
            }
        });

        this.speechRecognition.onStatusChange((isListening, message) => {
            if (!this.elements.speechStatus) return;

            if (isListening) {
                this.elements.speechStatus.classList.remove('hidden');
                const textElem = this.elements.speechStatus.querySelector('.status-text');
                if (textElem) textElem.textContent = message || 'Listening...';
                if (this.elements.micBtn) this.elements.micBtn.classList.add('active');
            } else {
                this.elements.speechStatus.classList.add('hidden');
                if (this.elements.micBtn) this.elements.micBtn.classList.remove('active');
            }
        });
    }

    async handleTranslate() {
        const text = this.elements.textInput ? this.elements.textInput.value.trim() : '';

        if (!text) {
            alert('Please enter some text or use voice input first.');
            return;
        }

        if (this.isProcessing) return;
        this.isProcessing = true;

        this.showProgress(true, 'Analyzing text...');

        try {
            this.updateProgress(30, 'Resolving signs...');
            const result = await this.apiService.translate(text, this.currentLanguage);

            this.updateProgress(80, 'Rendering signs...');
            this.mediaPlayer.displaySigns(result.signs, this.currentMode);

            this.updateProgress(100, 'Done');
            setTimeout(() => this.showProgress(false), 500);
        } catch (error) {
            console.error('Translation error:', error);
            alert('An error occurred during translation. Please try again.');
            this.showProgress(false);
        } finally {
            this.isProcessing = false;
        }
    }

    handleMicClick() {
        if (this.speechRecognition.isListening) {
            this.speechRecognition.stop();
        } else {
            this.speechRecognition.start();
        }
    }

    handleClear() {
        if (this.elements.textInput) {
            this.elements.textInput.value = '';
        }
        this.mediaPlayer.clear();
        this.showProgress(false);
    }

    handleLanguageChange(lang) {
        this.currentLanguage = lang;

        if (this.elements.languageToggles) {
            this.elements.languageToggles.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.lang === lang);
            });
        }

        if (this.elements.currentLanguage) {
            const label = lang === 'asl'
                ? 'American Sign Language (ASL)'
                : 'Indian Sign Language (ISL)';
            this.elements.currentLanguage.textContent = label;
        }

        // Re-translate if text is present
        if (this.elements.textInput && this.elements.textInput.value.trim()) {
            this.handleTranslate();
        }
    }

    handleModeChange(mode) {
        this.currentMode = mode;
        this.mediaPlayer.setMode(mode);

        if (this.elements.modeToggles) {
            this.elements.modeToggles.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.mode === mode);
            });
        }

        // If we have an existing playlist, re-render in the new mode
        if (this.mediaPlayer.playlist && this.mediaPlayer.playlist.length) {
            this.mediaPlayer.displaySigns(this.mediaPlayer.playlist, mode);
        }
    }

    showProgress(show, message = 'Processing...') {
        if (!this.elements.statusBar) return;

        if (show) {
            this.elements.statusBar.classList.remove('hidden');
            if (this.elements.statusText) this.elements.statusText.textContent = message;
            if (this.elements.progressFill) this.elements.progressFill.style.width = '10%';
        } else {
            this.elements.statusBar.classList.add('hidden');
            if (this.elements.progressFill) this.elements.progressFill.style.width = '0%';
        }
    }

    updateProgress(percent, message) {
        if (this.elements.progressFill) {
            this.elements.progressFill.style.width = `${percent}%`;
        }
        if (message && this.elements.statusText) {
            this.elements.statusText.textContent = message;
        }
    }
}

// Instantiate application
const app = new App();
export default app;
