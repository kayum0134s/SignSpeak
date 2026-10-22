/**
 * Text Processor Utility Module
 * Handles text normalization, contraction expansion, Hindi transliteration,
 * and greedy longest-match tokenization for sign translation.
 */

export class TextProcessor {
    constructor() {
        // Common English contractions to expand deterministically
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

        // Multi-word phrases mapping to single sign demonstrations
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

        // Hindi/Indian phrases for ISL (maps transliterated idioms to English equivalents)
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
     * Main processing pipeline
     * @param {string} text - Raw input text
     * @returns {object} - Processed text with structured tokens
     */
    process(text) {
        if (!text || typeof text !== 'string') {
            return { tokens: [], original: '' };
        }

        // Clean and normalize
        let processed = this.clean(text);
        processed = this.expandContractions(processed);

        // Check for Hindi phrase mappings
        processed = this.translateHindiPhrases(processed);

        // Tokenize into phrases, words, and letter fallbacks
        const tokens = this.tokenize(processed);

        return {
            original: text,
            normalized: processed,
            tokens: tokens
        };
    }

    /**
     * Clean and normalize raw text input
     * @param {string} text
     * @returns {string}
     */
    clean(text) {
        return text
            .toLowerCase()
            .trim()
            // Keep letters, numbers, spaces, and Hindi Devanagari characters
            .replace(/[^\w\s\u0900-\u097F']/g, '')
            .replace(/\s+/g, ' ');
    }

    /**
     * Expand common English contractions
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
     * Translate Hindi transliterations to semantic English equivalents
     * @param {string} text
     * @returns {string}
     */
    translateHindiPhrases(text) {
        let translated = text;
        for (const [hindi, english] of Object.entries(this.hindiPhrases)) {
            const regex = new RegExp(`\\b${hindi}\\b`, 'gi');
            translated = translated.replace(regex, english);
        }
        return translated;
    }

    /**
     * Greedy longest-match tokenization algorithm
     * Priority: Multi-word phrases first -> Words -> Letters
     * @param {string} text
     * @returns {Array<object>}
     */
    tokenize(text) {
        const tokens = [];
        const words = text.split(' ').filter(w => w.length > 0);
        let i = 0;

        // Sort common phrases by word count (longest phrase first)
        const sortedPhrases = [...this.commonPhrases].sort(
            (a, b) => b.split(' ').length - a.split(' ').length
        );

        while (i < words.length) {
            let matched = false;

            // Greedy check for multi-word phrases starting at index i
            for (const phrase of sortedPhrases) {
                const phraseWords = phrase.split(' ');
                const phraseLength = phraseWords.length;

                if (i + phraseLength <= words.length) {
                    const candidate = words.slice(i, i + phraseLength).join(' ');

                    if (candidate === phrase) {
                        tokens.push({
                            type: 'phrase',
                            value: phrase,
                            words: phraseWords
                        });
                        i += phraseLength;
                        matched = true;
                        break;
                    }
                }
            }

            // If no phrase matched, emit word token
            if (!matched) {
                tokens.push({
                    type: 'word',
                    value: words[i]
                });
                i++;
            }
        }

        return tokens;
    }
}

export default TextProcessor;
