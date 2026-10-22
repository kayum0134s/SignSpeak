/**
 * SignSpeak - Global Runtime Configuration
 * Centralized settings for API endpoints, media paths, and feature toggles.
 */

const getApiBaseUrl = () => {
    // If running in development with explicit port 8000 or custom host
    if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;
        const port = window.location.port;

        // If accessed via backend port 8000 or standard relative API
        if (port === '8000') {
            return `${window.location.origin}/api/v1`;
        }
        
        // If accessed via another dev server (e.g. 3000, 5500), target backend at 8000
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return `http://${hostname}:8000/api/v1`;
        }

        // Production relative path
        return '/api/v1';
    }
    return 'http://localhost:8000/api/v1';
};

export const CONFIG = {
    API_BASE_URL: getApiBaseUrl(),
    DATA_MAPPING_URL: 'public/data/sign-mapping.json',
    FALLBACK_MAPPING_URL: '../data/sign-mapping.json',
    MEDIA_BASE_PATH: 'public/media/',
    DEFAULT_LANGUAGE: 'asl',
    DEFAULT_MODE: 'video',
    PLAYBACK_SPEEDS: [0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
    DEFAULT_SPEED: 1.0,
    ENABLE_BACKEND_TRANSLATION: true // Attempts FastAPI backend first, falls back to client
};

export default CONFIG;
