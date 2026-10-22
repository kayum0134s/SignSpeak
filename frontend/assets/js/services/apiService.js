/**
 * API Service Module
 * Handles client-server communication with the FastAPI backend.
 * Features automatic failover to client-side rule engine if backend is offline.
 */

import { CONFIG } from '../utils/config.js';
import { TextProcessor } from '../utils/textProcessor.js';
import { SignTranslator } from './signTranslator.js';

export class ApiService {
    constructor() {
        this.baseUrl = CONFIG.API_BASE_URL;
        this.backendAvailable = false;
        this.clientTextProcessor = new TextProcessor();
        this.clientSignTranslator = new SignTranslator();

        // Perform initial health check asynchronously
        this.checkHealth();
    }

    /**
     * Check backend health status
     */
    async checkHealth() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);

            const res = await fetch(`${this.baseUrl}/health`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (res.ok) {
                const data = await res.json();
                this.backendAvailable = true;
                console.log('✅ Backend API is active:', data);
                return { online: true, data };
            }
        } catch (e) {
            this.backendAvailable = false;
            // Silent fallback to client mode
            console.info('ℹ️ Backend API offline. Operating in autonomous client-side mode.');
        }

        return { online: false };
    }

    /**
     * Change dialect language for translation
     */
    setLanguage(language) {
        this.clientSignTranslator.setLanguage(language);
    }

    /**
     * Translate input text to sign language media references
     * @param {string} text - Raw user input
     * @param {string} language - 'asl' or 'isl'
     * @returns {Promise<{tokens: Array, signs: Array, source: string}>}
     */
    async translate(text, language = 'asl') {
        this.setLanguage(language);

        // Attempt Backend API if configured
        if (CONFIG.ENABLE_BACKEND_TRANSLATION) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 3000);

                const response = await fetch(`${this.baseUrl}/translate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, language }),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (response.ok) {
                    const result = await response.json();
                    this.backendAvailable = true;
                    // Format response to match frontend player requirements
                    return {
                        original: text,
                        normalized: result.normalized,
                        tokens: result.tokens,
                        signs: result.signs.map(s => ({
                            ...s,
                            path: this.clientSignTranslator.normalizePath(s.path)
                        })),
                        source: 'backend'
                    };
                }
            } catch (err) {
                console.warn('Backend request failed or timed out. Falling back to client-side engine.');
            }
        }

        // Autonomous Client-Side Fallback
        const processed = this.clientTextProcessor.process(text);
        const signs = await this.clientSignTranslator.translate(processed.tokens);

        return {
            original: text,
            normalized: processed.normalized,
            tokens: processed.tokens,
            signs: signs,
            source: 'client'
        };
    }
}

export default ApiService;
