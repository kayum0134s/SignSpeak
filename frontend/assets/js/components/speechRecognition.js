/**
 * Speech Recognition Component
 * Native Web Speech API wrapper with visual lifecycle callbacks and origin checking.
 */

export class SpeechRecognitionHandler {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.onResultCallback = null;
        this.onErrorCallback = null;
        this.onStatusChangeCallback = null;

        this.init();
    }

    /**
     * Check if Web Speech API is supported
     */
    isSupported() {
        return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    }

    /**
     * Initialize Speech Recognition instance
     */
    init() {
        if (!this.isSupported()) {
            console.warn('Web Speech API is not supported in this browser.');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        // Configuration
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        // Event Listeners
        this.recognition.onstart = () => {
            this.isListening = true;
            this.notifyStatus(true, 'Listening... Speak now.');
        };

        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            const activeText = finalTranscript || interimTranscript;
            if (this.onResultCallback && activeText) {
                this.onResultCallback(activeText, Boolean(finalTranscript));
            }
        };

        this.recognition.onerror = (event) => {
            this.isListening = false;
            console.error('Speech recognition error:', event.error);
            this.notifyStatus(false, `Error: ${event.error}`);

            if (this.onErrorCallback) {
                this.onErrorCallback(event.error);
            }
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.notifyStatus(false, 'Speech recognition stopped.');
        };
    }

    /**
     * Start speech recognition
     */
    start() {
        if (!this.recognition) {
            this.init();
        }

        if (!this.recognition) {
            alert('Voice input is not supported by your current browser. Please use Chrome, Edge, or Safari.');
            return false;
        }

        // Origin check for microphones
        if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            alert('Voice input requires a secure origin (HTTPS or localhost).');
            return false;
        }

        if (this.isListening) {
            this.stop();
            return false;
        }

        try {
            this.recognition.start();
            return true;
        } catch (error) {
            console.error('Failed to start speech recognition:', error);
            return false;
        }
    }

    /**
     * Stop speech recognition
     */
    stop() {
        if (this.recognition && this.isListening) {
            try {
                this.recognition.stop();
            } catch (e) {
                console.warn('Recognition stop error:', e);
            }
            this.isListening = false;
        }
    }

    /**
     * Register result callback
     */
    onResult(callback) {
        this.onResultCallback = callback;
    }

    /**
     * Register status change callback
     */
    onStatusChange(callback) {
        this.onStatusChangeCallback = callback;
    }

    /**
     * Register error callback
     */
    onError(callback) {
        this.onErrorCallback = callback;
    }

    /**
     * Notify status listeners
     */
    notifyStatus(isListening, message) {
        if (this.onStatusChangeCallback) {
            this.onStatusChangeCallback(isListening, message);
        }
    }
}

export default SpeechRecognitionHandler;
