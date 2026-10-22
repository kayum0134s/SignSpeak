/**
 * Media Generator Component
 * Generates dynamic fallback images using HTML5 Canvas API when static assets are missing.
 */

export class MediaGenerator {
    /**
     * Generate dynamic sign image using HTML5 Canvas
     * @param {string} text - The word or letter to generate sign for
     * @param {string} language - 'asl' or 'isl'
     * @returns {string} - Data URL of the generated image
     */
    generateSignImage(text, language = 'asl') {
        const canvas = document.createElement('canvas');
        canvas.width = 300;
        canvas.height = 300;
        const ctx = canvas.getContext('2d');

        // Draw background gradient
        const gradient = ctx.createLinearGradient(0, 0, 300, 300);
        if (language === 'asl') {
            gradient.addColorStop(0, '#1e3c72');
            gradient.addColorStop(1, '#2a5298');
        } else {
            gradient.addColorStop(0, '#ff9933');
            gradient.addColorStop(1, '#138808');
        }
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 300, 300);

        // Draw decorative border
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 8;
        ctx.strokeRect(10, 10, 280, 280);

        // Draw hand icon placeholder
        ctx.font = '72px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('✋', 150, 110);

        // Draw text label
        ctx.font = 'bold 28px sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
        ctx.shadowBlur = 4;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;

        const displayText = text.toUpperCase();
        // Truncate if too long
        const truncatedText = displayText.length > 14
            ? displayText.substring(0, 12) + '...'
            : displayText;

        ctx.fillText(truncatedText, 150, 200);

        // Reset shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;

        // Draw language indicator badge
        ctx.font = 'bold 14px sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.fillText(`[ ${language.toUpperCase()} SIGN ]`, 150, 245);

        return canvas.toDataURL('image/png');
    }

    /**
     * Create image element with dynamic fallback on error
     * @param {string} src - Image source URL
     * @param {string} alt - Alt text
     * @param {string} language - 'asl' or 'isl'
     * @returns {HTMLImageElement}
     */
    createImageWithFallback(src, alt, language = 'asl') {
        const img = document.createElement('img');
        img.alt = alt;
        img.className = 'sign-card-image';

        img.onerror = () => {
            console.warn(`Sign image not found at ${src}, generating dynamic fallback.`);
            img.src = this.generateSignImage(alt, language);
            img.onerror = null; // Prevent infinite error loop
        };

        img.src = src;
        return img;
    }
}

export default MediaGenerator;
