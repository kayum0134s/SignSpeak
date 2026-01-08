/**
 * Sign Translator Module
 * Maps text tokens to sign language media files
 */

class SignTranslator {
    constructor() {
        this.currentLanguage = 'asl';
        this.signMappings = null;
        this.loadPromise = this.loadMappings();
    }

    /**
     * Load sign mappings from JSON file
     */
    async loadMappings() {
        try {
            const response = await fetch('data/sign-mapping.json');
            this.signMappings = await response.json();
            return true;
        } catch (error) {
            console.error('Failed to load sign mappings:', error);
            // Fallback to default mappings if file doesn't exist
            this.signMappings = this.getDefaultMappings();
            return false;
        }
    }

    /**
     * Ensure mappings are loaded
     */
    async ensureLoaded() {
        await this.loadPromise;
    }

    /**
     * Set the current sign language
     * @param {string} language - 'asl' or 'isl'
     */
    setLanguage(language) {
        if (language === 'asl' || language === 'isl') {
            this.currentLanguage = language;
        }
    }

    /**
     * Translate tokens to sign media references
     * @param {array} tokens - Array of token objects from TextProcessor
     * @returns {array} - Array of sign media objects
     */
    async translate(tokens) {
        await this.ensureLoaded();

        const signs = [];
        const langMappings = this.signMappings[this.currentLanguage];

        for (const token of tokens) {
            if (token.type === 'phrase') {
                // Look for phrase mapping
                const phraseSign = langMappings[token.value];
                if (phraseSign) {
                    signs.push({
                        ...phraseSign,
                        label: token.value,
                        tokenType: 'phrase'
                    });
                } else {
                    // If phrase not found, break it into words
                    for (const word of token.words) {
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
     * Translate a single word
     * @param {string} word
     * @param {object} langMappings
     * @returns {array}
     */
    async translateWord(word, langMappings) {
        const signs = [];

        // Check if word exists in mappings
        if (langMappings[word]) {
            signs.push({
                ...langMappings[word],
                label: word,
                tokenType: 'word'
            });
        } else {
            // Fingerspell the word
            const letters = word.split('');
            for (const letter of letters) {
                if (langMappings[letter]) {
                    signs.push({
                        ...langMappings[letter],
                        label: letter,
                        tokenType: 'letter',
                        isFingerSpelling: true
                    });
                }
            }
        }

        return signs;
    }

    /**
     * Get default sign mappings (fallback)
     * This will be used if the JSON file fails to load
     */
    getDefaultMappings() {
        return {
            asl: {
                // Alphabet (will use generated images)
                'a': { type: 'image', path: 'media/signs/asl/alphabet/a.png', generated: true },
                'b': { type: 'image', path: 'media/signs/asl/alphabet/b.png', generated: true },
                'c': { type: 'image', path: 'media/signs/asl/alphabet/c.png', generated: true },
                'd': { type: 'image', path: 'media/signs/asl/alphabet/d.png', generated: true },
                'e': { type: 'image', path: 'media/signs/asl/alphabet/e.png', generated: true },
                'f': { type: 'image', path: 'media/signs/asl/alphabet/f.png', generated: true },
                'g': { type: 'image', path: 'media/signs/asl/alphabet/g.png', generated: true },
                'h': { type: 'image', path: 'media/signs/asl/alphabet/h.png', generated: true },
                'i': { type: 'image', path: 'media/signs/asl/alphabet/i.png', generated: true },
                'j': { type: 'image', path: 'media/signs/asl/alphabet/j.png', generated: true },
                'k': { type: 'image', path: 'media/signs/asl/alphabet/k.png', generated: true },
                'l': { type: 'image', path: 'media/signs/asl/alphabet/l.png', generated: true },
                'm': { type: 'image', path: 'media/signs/asl/alphabet/m.png', generated: true },
                'n': { type: 'image', path: 'media/signs/asl/alphabet/n.png', generated: true },
                'o': { type: 'image', path: 'media/signs/asl/alphabet/o.png', generated: true },
                'p': { type: 'image', path: 'media/signs/asl/alphabet/p.png', generated: true },
                'q': { type: 'image', path: 'media/signs/asl/alphabet/q.png', generated: true },
                'r': { type: 'image', path: 'media/signs/asl/alphabet/r.png', generated: true },
                's': { type: 'image', path: 'media/signs/asl/alphabet/s.png', generated: true },
                't': { type: 'image', path: 'media/signs/asl/alphabet/t.png', generated: true },
                'u': { type: 'image', path: 'media/signs/asl/alphabet/u.png', generated: true },
                'v': { type: 'image', path: 'media/signs/asl/alphabet/v.png', generated: true },
                'w': { type: 'image', path: 'media/signs/asl/alphabet/w.png', generated: true },
                'x': { type: 'image', path: 'media/signs/asl/alphabet/x.png', generated: true },
                'y': { type: 'image', path: 'media/signs/asl/alphabet/y.png', generated: true },
                'z': { type: 'image', path: 'media/signs/asl/alphabet/z.png', generated: true },

                // Common words (will use generated images for now)
                'hello': { type: 'image', path: 'media/signs/asl/common/hello.png', generated: true },
                'goodbye': { type: 'image', path: 'media/signs/asl/common/goodbye.png', generated: true },
                'please': { type: 'image', path: 'media/signs/asl/common/please.png', generated: true },
                'yes': { type: 'image', path: 'media/signs/asl/common/yes.png', generated: true },
                'no': { type: 'image', path: 'media/signs/asl/common/no.png', generated: true },
                'sorry': { type: 'image', path: 'media/signs/asl/common/sorry.png', generated: true },
                'help': { type: 'image', path: 'media/signs/asl/common/help.png', generated: true },
                'love': { type: 'image', path: 'media/signs/asl/common/love.png', generated: true },

                // Common phrases
                'thank you': { type: 'image', path: 'media/signs/asl/phrases/thank_you.png', generated: true },
                'how are you': { type: 'image', path: 'media/signs/asl/phrases/how_are_you.png', generated: true },
                'nice to meet you': { type: 'image', path: 'media/signs/asl/phrases/nice_to_meet_you.png', generated: true },
                'my name is': { type: 'image', path: 'media/signs/asl/phrases/my_name_is.png', generated: true },
                'good morning': { type: 'image', path: 'media/signs/asl/phrases/good_morning.png', generated: true },
            },
            isl: {
                // ISL Alphabet (similar structure)
                'a': { type: 'image', path: 'media/signs/isl/alphabet/a.png', generated: true },
                'b': { type: 'image', path: 'media/signs/isl/alphabet/b.png', generated: true },
                'c': { type: 'image', path: 'media/signs/isl/alphabet/c.png', generated: true },
                'd': { type: 'image', path: 'media/signs/isl/alphabet/d.png', generated: true },
                'e': { type: 'image', path: 'media/signs/isl/alphabet/e.png', generated: true },
                'f': { type: 'image', path: 'media/signs/isl/alphabet/f.png', generated: true },
                'g': { type: 'image', path: 'media/signs/isl/alphabet/g.png', generated: true },
                'h': { type: 'image', path: 'media/signs/isl/alphabet/h.png', generated: true },
                'i': { type: 'image', path: 'media/signs/isl/alphabet/i.png', generated: true },
                'j': { type: 'image', path: 'media/signs/isl/alphabet/j.png', generated: true },
                'k': { type: 'image', path: 'media/signs/isl/alphabet/k.png', generated: true },
                'l': { type: 'image', path: 'media/signs/isl/alphabet/l.png', generated: true },
                'm': { type: 'image', path: 'media/signs/isl/alphabet/m.png', generated: true },
                'n': { type: 'image', path: 'media/signs/isl/alphabet/n.png', generated: true },
                'o': { type: 'image', path: 'media/signs/isl/alphabet/o.png', generated: true },
                'p': { type: 'image', path: 'media/signs/isl/alphabet/p.png', generated: true },
                'q': { type: 'image', path: 'media/signs/isl/alphabet/q.png', generated: true },
                'r': { type: 'image', path: 'media/signs/isl/alphabet/r.png', generated: true },
                's': { type: 'image', path: 'media/signs/isl/alphabet/s.png', generated: true },
                't': { type: 'image', path: 'media/signs/isl/alphabet/t.png', generated: true },
                'u': { type: 'image', path: 'media/signs/isl/alphabet/u.png', generated: true },
                'v': { type: 'image', path: 'media/signs/isl/alphabet/v.png', generated: true },
                'w': { type: 'image', path: 'media/signs/isl/alphabet/w.png', generated: true },
                'x': { type: 'image', path: 'media/signs/isl/alphabet/x.png', generated: true },
                'y': { type: 'image', path: 'media/signs/isl/alphabet/y.png', generated: true },
                'z': { type: 'image', path: 'media/signs/isl/alphabet/z.png', generated: true },

                // Common words
                'hello': { type: 'image', path: 'media/signs/isl/common/hello.png', generated: true },
                'goodbye': { type: 'image', path: 'media/signs/isl/common/goodbye.png', generated: true },
                'please': { type: 'image', path: 'media/signs/isl/common/please.png', generated: true },
                'yes': { type: 'image', path: 'media/signs/isl/common/yes.png', generated: true },
                'no': { type: 'image', path: 'media/signs/isl/common/no.png', generated: true },
                'sorry': { type: 'image', path: 'media/signs/isl/common/sorry.png', generated: true },
                'help': { type: 'image', path: 'media/signs/isl/common/help.png', generated: true },
                'love': { type: 'image', path: 'media/signs/isl/common/love.png', generated: true },

                // Common phrases
                'thank you': { type: 'image', path: 'media/signs/isl/phrases/thank_you.png', generated: true },
                'how are you': { type: 'image', path: 'media/signs/isl/phrases/how_are_you.png', generated: true },
                'nice to meet you': { type: 'image', path: 'media/signs/isl/phrases/nice_to_meet_you.png', generated: true },
                'my name is': { type: 'image', path: 'media/signs/isl/phrases/my_name_is.png', generated: true },
                'good morning': { type: 'image', path: 'media/signs/isl/phrases/good_morning.png', generated: true },
            }
        };
    }
}

export default SignTranslator;
