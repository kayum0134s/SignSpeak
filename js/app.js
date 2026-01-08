/**
 * Main Application Controller
 * Coordinates all modules and handles UI interactions
 */

import SpeechRecognitionHandler from './speechRecognition.js';
import TextProcessor from './textProcessor.js';
import SignTranslator from './signTranslator.js';
import MediaPlayer from './mediaPlayer.js';
import MediaGenerator from './mediaGenerator.js';

class App {
    constructor() {
        this.speechRecognition = new SpeechRecognitionHandler();
        this.textProcessor = new TextProcessor();
        this.signTranslator = new SignTranslator();
        this.mediaPlayer = new MediaPlayer();
        this.mediaGenerator = new MediaGenerator();

        this.currentLanguage = 'asl';
        this.isProcessing = false;

        this.init();
    }

    async init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }

    setupUI() {
        // Get DOM elements
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

        // Initialize media player with DOM elements
        this.mediaPlayer.init({
            galleryGrid: this.elements.galleryGrid,
            videoPlayer: this.elements.signVideo,
            galleryView: this.elements.galleryView,
            videoView: this.elements.videoView,
            outputDisplay: this.elements.outputDisplay
        });

        // Set up event listeners
        this.setupEventListeners();

        // Set up speech recognition callbacks
        this.setupSpeechRecognition();
    }

    setupEventListeners() {
        // Translate button
        this.elements.translateBtn.addEventListener('click', () => this.handleTranslate());

        // Clear button
        this.elements.clearBtn.addEventListener('click', () => this.handleClear());

        // Microphone button
        this.elements.micBtn.addEventListener('click', () => this.handleMicClick());

        // Language toggles
        this.elements.languageToggles.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const lang = e.currentTarget.dataset.lang;
                if (lang) this.handleLanguageChange(lang);
            });
        });

        // Mode toggles
        this.elements.modeToggles.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleModeChange(e.target.dataset.mode));
        });

        // Video controls
        if (this.elements.playBtn) {
            this.elements.playBtn.addEventListener('click', () => this.mediaPlayer.play());
        }

        if (this.elements.pauseBtn) {
            this.elements.pauseBtn.addEventListener('click', () => this.mediaPlayer.pause());
        }

        if (this.elements.speedSlider) {
            this.elements.speedSlider.addEventListener('input', (e) => {
                const speed = parseFloat(e.target.value);
                this.elements.speedValue.textContent = `${speed}x`;
                this.mediaPlayer.setSpeed(speed);
            });
        }

        // Download buttons


        // Enter key in text input
        this.elements.textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleTranslate();
            }
        });

        // About modal
        if (this.elements.aboutBtn) {
            this.elements.aboutBtn.addEventListener('click', () => this.openAboutModal());
        }

        if (this.elements.modalClose) {
            this.elements.modalClose.addEventListener('click', () => this.closeAboutModal());
        }

        if (this.elements.aboutModal) {
            // Close modal when clicking outside
            this.elements.aboutModal.addEventListener('click', (e) => {
                if (e.target === this.elements.aboutModal) {
                    this.closeAboutModal();
                }
            });
        }
    }

    setupSpeechRecognition() {
        // Handle speech results
        this.speechRecognition.onResult = (result) => {
            if (result.isFinal) {
                // Append final text
                const currentText = this.elements.textInput.value;
                this.elements.textInput.value = currentText + (currentText ? ' ' : '') + result.final;
            } else {
                // Show interim results in status
                this.updateSpeechStatus(`Listening: "${result.interim}"`);
            }
        };

        // Handle errors
        this.speechRecognition.onError = (error) => {
            console.error('Speech recognition error:', error);
            this.showError(error.message);
            this.hideSpeechStatus();
        };

        // Handle status changes
        this.speechRecognition.onStatusChange = (status) => {
            if (status.status === 'listening') {
                this.showSpeechStatus();
            } else if (status.status === 'stopped' || status.status === 'error') {
                this.hideSpeechStatus();
            }
        };
    }

    async handleTranslate() {
        const text = this.elements.textInput.value.trim();

        if (!text) {
            this.showError('Please enter some text or use voice input');
            return;
        }

        if (this.isProcessing) {
            return;
        }

        this.isProcessing = true;
        this.showStatus('Processing text...', 20);

        try {
            // Process text
            const processed = this.textProcessor.process(text);
            this.showStatus('Translating to sign language...', 40);

            // Translate to signs
            const signs = await this.signTranslator.translate(processed.tokens);
            this.showStatus('Loading sign media...', 60);

            // Generate any missing images
            for (const sign of signs) {
                if (sign.generated) {
                    sign.path = await this.mediaGenerator.getSignImage(sign, this.currentLanguage);
                }
            }

            this.showStatus('Displaying signs...', 80);

            // Display signs
            await this.mediaPlayer.displaySigns(signs);



            this.hideStatus();
        } catch (error) {
            console.error('Translation error:', error);
            this.showError('Failed to translate text. Please try again.');
        } finally {
            this.isProcessing = false;
        }
    }

    handleClear() {
        this.elements.textInput.value = '';
        this.mediaPlayer.showPlaceholder();
    }

    handleMicClick() {
        if (this.speechRecognition.isListening) {
            this.speechRecognition.stop();
        } else {
            const started = this.speechRecognition.start();
            if (!started && !this.speechRecognition.isSupported()) {
                this.showError('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
            }
        }
    }

    handleLanguageChange(language) {
        if (language === this.currentLanguage) return;

        this.currentLanguage = language;
        this.signTranslator.setLanguage(language);

        // Update UI
        this.elements.languageToggles.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === language);
        });

        // Update footer text
        const languageNames = {
            'asl': 'American Sign Language (ASL)',
            'isl': 'Indian Sign Language (ISL)'
        };
        if (this.elements.currentLanguage) {
            this.elements.currentLanguage.textContent = languageNames[language] || language.toUpperCase();
        }

        // Re-translate if there's current content
        const signs = this.mediaPlayer.getCurrentSigns();
        if (signs.length > 0) {
            this.handleTranslate();
        }
    }

    handleModeChange(mode) {
        this.mediaPlayer.setMode(mode);

        // Update UI
        this.elements.modeToggles.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
    }

    async handleDownloadVideo() {
        this.showStatus('Generating video...', 0);

        // This is a placeholder - full implementation would compile signs into video
        setTimeout(() => {
            this.showError('Video download feature coming soon!');
            this.hideStatus();
        }, 1000);
    }

    async handleDownloadImages() {
        this.showStatus('Preparing images...', 0);

        // This is a placeholder - full implementation would create ZIP of images
        setTimeout(() => {
            this.showError('Image download feature coming soon!');
            this.hideStatus();
        }, 1000);
    }

    // UI Helper Methods
    showStatus(message, progress) {
        this.elements.statusBar.classList.remove('hidden');
        this.elements.statusText.textContent = message;
        this.elements.progressFill.style.width = `${progress}%`;
    }

    hideStatus() {
        setTimeout(() => {
            this.elements.statusBar.classList.add('hidden');
            this.elements.progressFill.style.width = '0%';
        }, 500);
    }

    showSpeechStatus() {
        this.elements.speechStatus.classList.remove('hidden');
    }

    hideSpeechStatus() {
        this.elements.speechStatus.classList.add('hidden');
    }

    updateSpeechStatus(text) {
        const statusTextEl = this.elements.speechStatus.querySelector('.status-text');
        if (statusTextEl) {
            statusTextEl.textContent = text;
        }
    }

    showError(message) {
        // Simple alert for now - could be replaced with nicer notification
        alert(message);
    }

    openAboutModal() {
        if (this.elements.aboutModal) {
            this.elements.aboutModal.classList.remove('hidden');
        }
    }

    closeAboutModal() {
        if (this.elements.aboutModal) {
            this.elements.aboutModal.classList.add('hidden');
        }
    }
}

// Initialize app when script loads
const app = new App();

export default App;
