/**
 * Speech Recognition Module
 * Handles speech-to-text conversion using Web Speech API
 */

class SpeechRecognitionHandler {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.onResult = null;
        this.onError = null;
        this.onStatusChange = null;
        
        this.initializeRecognition();
    }
    
    initializeRecognition() {
        // Check browser compatibility
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.error('Speech Recognition API not supported in this browser');
            return false;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        // Set up event listeners
        this.recognition.onstart = () => {
            this.isListening = true;
            if (this.onStatusChange) {
                this.onStatusChange({ status: 'listening', message: 'Listening...' });
            }
        };
        
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }
            
            if (this.onResult) {
                this.onResult({
                    final: finalTranscript.trim(),
                    interim: interimTranscript.trim(),
                    isFinal: finalTranscript.length > 0
                });
            }
        };
        
        this.recognition.onerror = (event) => {
            this.isListening = false;
            const errorMessage = this.getErrorMessage(event.error);
            
            if (this.onError) {
                this.onError({ error: event.error, message: errorMessage });
            }
            
            if (this.onStatusChange) {
                this.onStatusChange({ status: 'error', message: errorMessage });
            }
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            if (this.onStatusChange) {
                this.onStatusChange({ status: 'stopped', message: 'Stopped listening' });
            }
        };
        
        return true;
    }
    
    start() {
        if (!this.recognition) {
            if (this.onError) {
                this.onError({ 
                    error: 'not-supported', 
                    message: 'Speech recognition is not supported in your browser. Please use Chrome or Edge.' 
                });
            }
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
            console.error('Error starting speech recognition:', error);
            if (this.onError) {
                this.onError({ error: 'start-failed', message: 'Failed to start speech recognition' });
            }
            return false;
        }
    }
    
    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    getErrorMessage(errorCode) {
        const errorMessages = {
            'no-speech': 'No speech detected. Please try again.',
            'audio-capture': 'Microphone access denied or not available.',
            'not-allowed': 'Microphone permission denied. Please allow microphone access.',
            'network': 'Network error occurred. Please check your connection.',
            'aborted': 'Speech recognition was aborted.',
            'language-not-supported': 'Language not supported.',
        };
        
        return errorMessages[errorCode] || `Speech recognition error: ${errorCode}`;
    }
    
    isSupported() {
        return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
    }
}

export default SpeechRecognitionHandler;
