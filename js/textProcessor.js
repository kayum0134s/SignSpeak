/**
 * Text Processor Module
 * Handles text normalization, tokenization, and preparation for sign translation
 */

class TextProcessor {
    constructor() {
        // Common contractions to expand
        this.contractions = {
            "i'm": "i am",
            "you're": "you are",
            "he's": "he is",
            "she's": "she is",
            "it's": "it is",
            "we're": "we are",
            "they're": "they are",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "won't": "will not",
            "wouldn't": "would not",
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "can't": "can not",
            "couldn't": "could not",
            "shouldn't": "should not",
            "mightn't": "might not",
            "mustn't": "must not"
        };

        // Common multi-word phrases that map to single signs
        this.commonPhrases = [
            "how are you",
            "thank you",
            "thanks you",
            "nice to meet you",
            "good morning",
            "good afternoon",
            "good evening",
            "good night",
            "see you later",
            "my name is",
            "what is your name",
            "i love you",
            "excuse me",
            "i'm sorry",
            "you're welcome",
            "pleased to meet you",
            "how old are you",
            "where are you from",
            "have a good day",
            "what are you doing"
        ];

        // Hindi/Indian phrases for ISL (maps to English equivalents)
        this.hindiPhrases = {
            "aapka naam kya hai": "what is your name",
            "aapka naam kya he": "what is your name",
            "tumhara naam kya hai": "what is your name",
            "aap kaise hain": "how are you",
            "aap kaise ho": "how are you",
            "tum kaise ho": "how are you",
            "kaise hain aap": "how are you",
            "namaste": "hello",
            "namaskar": "hello",
            "shukriya": "thank you",
            "dhanyavad": "thank you",
            "subah bakhair": "good morning",
            "shubh prabhat": "good morning",
            "shubh sandhya": "good evening",
            "shubh ratri": "good night",
            "alvida": "goodbye",
            "phir milenge": "see you later",
            "mera naam hai": "my name is",
            "aap kya kar rahe hain": "what are you doing",
            "aap kya kar rahi hain": "what are you doing",
            "maaf kijiye": "excuse me",
            "maaf karna": "i'm sorry"
        };
    }

    /**
     * Main processing function
     * @param {string} text - Raw input text
     * @returns {object} - Processed text with tokens
     */
    process(text) {
        if (!text || typeof text !== 'string') {
            return { tokens: [], original: '' };
        }

        // Clean and normalize
        let processed = this.clean(text);
        processed = this.expandContractions(processed);

        // Tokenize with phrase detection
        const tokens = this.tokenize(processed);

        return {
            tokens: tokens,
            original: text,
            processed: processed
        };
    }

    /**
     * Clean and normalize text
     * @param {string} text
     * @returns {string}
     */
    clean(text) {
        // Convert to lowercase
        text = text.toLowerCase();

        // Remove extra whitespace
        text = text.replace(/\s+/g, ' ').trim();

        // Remove special characters but keep letters, numbers, spaces, and basic punctuation
        // Also support Hindi/Devanagari characters (Unicode range)
        text = text.replace(/[^a-z0-9\s.,!?'\u0900-\u097F-]/g, '');

        return text;
    }

    /**
     * Expand contractions
     * @param {string} text
     * @returns {string}
     */
    expandContractions(text) {
        let expanded = text;

        for (const [contraction, expansion] of Object.entries(this.contractions)) {
            const regex = new RegExp(`\\b${contraction}\\b`, 'gi');
            expanded = expanded.replace(regex, expansion);
        }

        return expanded;
    }

    /**
     * Tokenize text with phrase detection
     * @param {string} text
     * @returns {array} - Array of tokens (words or phrases)
     */
    tokenize(text) {
        const tokens = [];
        let remaining = text;

        // First, check for Hindi phrases and convert to English equivalents
        for (const [hindiPhrase, englishPhrase] of Object.entries(this.hindiPhrases)) {
            if (remaining.includes(hindiPhrase)) {
                remaining = remaining.replace(hindiPhrase, englishPhrase);
            }
        }

        // Now process with standard English phrase detection
        while (remaining.length > 0) {
            let matched = false;

            // Sort phrases by length (longest first) for better matching
            const sortedPhrases = this.commonPhrases.sort((a, b) => b.length - a.length);

            for (const phrase of sortedPhrases) {
                if (remaining.startsWith(phrase)) {
                    tokens.push({
                        type: 'phrase',
                        value: phrase,
                        words: phrase.split(' ')
                    });
                    remaining = remaining.slice(phrase.length).trim();
                    matched = true;
                    break;
                }
            }

            // If no phrase matched, take the next word
            if (!matched) {
                const match = remaining.match(/^([a-z0-9\u0900-\u097F'-]+)/);
                if (match) {
                    const word = match[1];
                    tokens.push({
                        type: 'word',
                        value: word
                    });
                    remaining = remaining.slice(word.length).trim();
                } else {
                    // Skip punctuation or unknown characters
                    remaining = remaining.slice(1).trim();
                }
            }
        }

        return tokens;
    }

    /**
     * Split text into sentences
     * @param {string} text
     * @returns {array}
     */
    splitSentences(text) {
        return text
            .split(/[.!?]+/)
            .map(s => s.trim())
            .filter(s => s.length > 0);
    }
}

export default TextProcessor;
