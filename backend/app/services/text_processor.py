"""
Deterministic Text Processor Service
Python implementation mirroring client-side textProcessor.js.
Performs normalization, contraction expansion, Hindi transliteration,
and greedy longest-match tokenization.
"""

import re
from typing import List, Dict, Any, Tuple

class TextProcessor:
    def __init__(self):
        # 34 standard English contractions
        self.contractions: Dict[str, str] = {
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
        }

        # Multi-word idioms with verified sign demonstrations
        self.common_phrases: List[str] = [
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
        ]

        # Hindi/Indian phrases mapped to semantic English equivalents
        self.hindi_phrases: Dict[str, str] = {
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
        }

    def clean(self, text: str) -> str:
        """Strip punctuation, preserve alphanumerics, spaces, and Hindi Devanagari Unicode."""
        lowered = text.lower().strip()
        # Keep letters, numbers, spaces, apostrophes, and Devanagari range \u0900-\u097F
        cleaned = re.sub(r"[^\w\s\u0900-\u097F']", "", lowered)
        collapsed = re.sub(r"\s+", " ", cleaned)
        return collapsed

    def expand_contractions(self, text: str) -> str:
        """Expand English contractions using word boundary matching."""
        result = text
        for contraction, expansion in self.contractions.items():
            pattern = rf"\b{re.escape(contraction)}\b"
            result = re.sub(pattern, expansion, result, flags=re.IGNORECASE)
        return result

    def translate_hindi(self, text: str) -> str:
        """Replace Hindi transliterated idioms with canonical English phrases."""
        result = text
        for hindi, english in self.hindi_phrases.items():
            pattern = rf"\b{re.escape(hindi)}\b"
            result = re.sub(pattern, english, result, flags=re.IGNORECASE)
        return result

    def tokenize(self, text: str) -> List[Dict[str, Any]]:
        """
        Greedy Longest-Match-First Tokenization.
        Prioritizes multi-word phrases over single words.
        """
        tokens: List[Dict[str, Any]] = []
        words = [w for w in text.split(" ") if w]
        i = 0

        # Sort phrases by word count descending
        sorted_phrases = sorted(self.common_phrases, key=lambda p: len(p.split(" ")), reverse=True)

        while i < len(words):
            matched = False

            for phrase in sorted_phrases:
                phrase_words = phrase.split(" ")
                phrase_len = len(phrase_words)

                if i + phrase_len <= len(words):
                    candidate = " ".join(words[i:i + phrase_len])
                    if candidate == phrase:
                        tokens.append({
                            "type": "phrase",
                            "value": phrase,
                            "words": phrase_words
                        })
                        i += phrase_len
                        matched = True
                        break

            if not matched:
                tokens.append({
                    "type": "word",
                    "value": words[i]
                })
                i += 1

        return tokens

    def process(self, text: str) -> Dict[str, Any]:
        """Main processing pipeline returning normalized text and token list."""
        if not text or not isinstance(text, str):
            return {"original": "", "normalized": "", "tokens": []}

        cleaned = self.clean(text)
        expanded = self.expand_contractions(cleaned)
        translated = self.translate_hindi(expanded)
        tokens = self.tokenize(translated)

        return {
            "original": text,
            "normalized": translated,
            "tokens": tokens
        }

# Global instance for reuse
text_processor = TextProcessor()
