/**
 * Sign Translator Service (Client-Side)
 * Loads sign mapping configuration and resolves linguistic tokens to media assets.
 * Operates offline or as a fallback when backend service is unavailable.
 */

import { CONFIG } from '../utils/config.js';

export class SignTranslator {
    constructor() {
        this.currentLanguage = CONFIG.DEFAULT_LANGUAGE;
        this.signMappings = null;
        this.loadPromise = this.loadMappings();
    }

    /**
     * Normalize media paths to match frontend structure
     * E.g. 'media/signs/asl/...' -> 'public/media/signs/asl/...'
     */
    normalizePath(rawPath) {
        if (!rawPath) return '';
        // If already pointing to public or absolute URL
        if (rawPath.startsWith('public/') || rawPath.startsWith('http://') || rawPath.startsWith('https://')) {
            return rawPath;
        }
        if (rawPath.startsWith('media/')) {
            return `public/${rawPath}`;
        }
        return `public/media/${rawPath}`;
    }

    /**
     * Load sign mappings from JSON config file
     */
    async loadMappings() {
        // Primary candidate paths to attempt
        const candidates = [
            '../data/sign-mapping.json',
            'public/data/sign-mapping.json',
            '/data/sign-mapping.json',
            'data/sign-mapping.json'
        ];

        for (const candidate of candidates) {
            try {
                const response = await fetch(candidate);
                if (response.ok) {
                    this.signMappings = await response.json();
                    return true;
                }
            } catch (err) {
                // Try next candidate
            }
        }

        console.warn('Could not fetch external sign-mapping.json; initializing default fallback mappings.');
        this.signMappings = this.getDefaultMappings();
        return false;
    }

    async ensureLoaded() {
        await this.loadPromise;
    }

    setLanguage(language) {
        if (language === 'asl' || language === 'isl') {
            this.currentLanguage = language;
        }
    }

    /**
     * Translate an array of tokens to visual sign objects
     * @param {Array<object>} tokens
     * @returns {Promise<Array<object>>}
     */
    async translate(tokens) {
        await this.ensureLoaded();
        const signs = [];
        const langMappings = (this.signMappings && this.signMappings[this.currentLanguage]) || {};

        for (const token of tokens) {
            if (token.type === 'phrase') {
                const phraseSign = langMappings[token.value];
                if (phraseSign) {
                    signs.push({
                        ...phraseSign,
                        path: this.normalizePath(phraseSign.path),
                        label: token.value,
                        tokenType: 'phrase',
                        language: this.currentLanguage
                    });
                } else {
                    // Fall back to constituent words
                    const constituentWords = token.words || token.value.split(' ');
                    for (const word of constituentWords) {
                        const wordSigns = await this.translateWord(word, langMappings);
                        signs.push(...wordSigns);
                    }
                }
            } else if (token.type === 'word') {
                const wordSigns = await this.translateWord(token.value, langMappings);
                signs.push(...wordSigns);
            }
        }

        return signs;
    }

    /**
     * Translate a single word with fingerspelling fallback
     */
    async translateWord(word, langMappings) {
        const signs = [];
        const lowerWord = word.toLowerCase();

        if (langMappings[lowerWord]) {
            signs.push({
                ...langMappings[lowerWord],
                path: this.normalizePath(langMappings[lowerWord].path),
                label: lowerWord,
                tokenType: 'word',
                language: this.currentLanguage
            });
        } else {
            // Fingerspell letter-by-letter
            const letterSigns = this.fingerspell(lowerWord, langMappings);
            signs.push(...letterSigns);
        }

        return signs;
    }

    /**
     * Fingerspell a word into individual alphabet signs
     */
    fingerspell(word, langMappings) {
        const signs = [];
        const letters = word.toLowerCase().split('');

        for (const letter of letters) {
            if (/[a-z]/.test(letter)) {
                if (langMappings[letter]) {
                    signs.push({
                        ...langMappings[letter],
                        path: this.normalizePath(langMappings[letter].path),
                        label: letter.toUpperCase(),
                        tokenType: 'letter',
                        language: this.currentLanguage
                    });
                } else {
                    signs.push({
                        type: 'image',
                        path: `public/media/signs/asl/alphabet/${letter}.jpg`,
                        label: letter.toUpperCase(),
                        tokenType: 'letter',
                        generated: false,
                        language: this.currentLanguage
                    });
                }
            }
        }

        return signs;
    }

    /**
     * Built-in minimal fallback mappings if JSON is missing
     */
    getDefaultMappings() {
        const alphabet = 'abcdefghijklmnopqrstuvwxyz'.split('');
        const asl = {};
        const isl = {};

        alphabet.forEach(letter => {
            asl[letter] = {
                type: 'image',
                path: `public/media/signs/asl/alphabet/${letter}.jpg`,
                generated: false
            };
            isl[letter] = {
                type: 'image',
                path: `public/media/signs/asl/alphabet/${letter}.jpg`,
                generated: false
            };
        });

        // Add core verified phrases
        const defaultPhrases = [
            "good morning", "good evening", "how are you", "what is your name",
            "what are you doing", "have a good day", "monday", "tuesday",
            "wednesday", "thursday", "friday", "saturday", "sunday"
        ];

        defaultPhrases.forEach(p => {
            asl[p] = {
                type: 'video',
                path: `public/media/signs/asl/phrases/${p.charAt(0).toUpperCase() + p.slice(1)}.mp4`,
                generated: false
            };
            isl[p] = {
                type: 'video',
                path: `public/media/signs/asl/phrases/${p.charAt(0).toUpperCase() + p.slice(1)}.mp4`,
                generated: false
            };
        });

        return { asl, isl };
    }
}

export default SignTranslator;
