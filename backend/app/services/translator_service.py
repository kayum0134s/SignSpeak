"""
Sign Translator Service (Backend)
Loads sign-mapping.json and resolves linguistic tokens to media assets with fingerspelling fallback.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.app.utils.config import DATA_MAPPING_FILE
from backend.app.models.schemas import SignItem, TokenItem

class TranslatorService:
    def __init__(self, mapping_path: Optional[Path] = None):
        self.mapping_path = mapping_path or DATA_MAPPING_FILE
        self.mappings: Dict[str, Dict[str, Any]] = {"asl": {}, "isl": {}}
        self.load_mappings()

    def load_mappings(self) -> bool:
        """Load JSON mapping file from disk."""
        if self.mapping_path.exists():
            try:
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    self.mappings = json.load(f)
                return True
            except Exception as e:
                print(f"⚠️ Error parsing sign mappings from {self.mapping_path}: {e}")
        else:
            print(f"⚠️ Mapping file not found at {self.mapping_path}")
        return False

    def get_stats(self) -> Dict[str, int]:
        """Return counts of registered signs."""
        return {
            "total_asl_signs": len(self.mappings.get("asl", {})),
            "total_isl_signs": len(self.mappings.get("isl", {}))
        }

    def normalize_media_path(self, raw_path: str) -> str:
        """Ensure media path uses frontend public convention."""
        if not raw_path:
            return ""
        if raw_path.startswith("public/") or raw_path.startswith("http://") or raw_path.startswith("https://"):
            return raw_path
        if raw_path.startswith("media/"):
            return f"public/{raw_path}"
        return f"public/media/{raw_path}"

    def fingerspell(self, word: str, language: str, lang_map: Dict[str, Any]) -> List[SignItem]:
        """Decompose unknown word into alphabet characters."""
        signs: List[SignItem] = []
        for char in word.lower():
            if 'a' <= char <= 'z':
                if char in lang_map:
                    item = lang_map[char]
                    signs.append(SignItem(
                        type=item.get("type", "image"),
                        path=self.normalize_media_path(item.get("path", "")),
                        label=char.upper(),
                        tokenType="letter",
                        language=language,
                        generated=item.get("generated", False)
                    ))
                else:
                    signs.append(SignItem(
                        type="image",
                        path=f"public/media/signs/asl/alphabet/{char}.jpg",
                        label=char.upper(),
                        tokenType="letter",
                        language=language,
                        generated=False
                    ))
        return signs

    def translate(self, tokens: List[Dict[str, Any]], language: str = "asl") -> List[SignItem]:
        """
        Translate structured tokens to SignItem objects.
        Cascade: Phrase -> Word -> Character Fingerspelling.
        """
        signs: List[SignItem] = []
        target_lang = "isl" if language.lower() == "isl" else "asl"
        lang_map = self.mappings.get(target_lang, {})

        for token in tokens:
            t_type = token.get("type", "word")
            t_value = token.get("value", "").lower()

            if t_type == "phrase":
                if t_value in lang_map:
                    item = lang_map[t_value]
                    signs.append(SignItem(
                        type=item.get("type", "video"),
                        path=self.normalize_media_path(item.get("path", "")),
                        label=t_value,
                        tokenType="phrase",
                        language=target_lang,
                        generated=item.get("generated", False)
                    ))
                else:
                    # Deconstruct phrase into individual words
                    words = token.get("words") or t_value.split(" ")
                    for word in words:
                        signs.extend(self._translate_word(word, target_lang, lang_map))

            elif t_type == "word":
                signs.extend(self._translate_word(t_value, target_lang, lang_map))

        return signs

    def _translate_word(self, word: str, language: str, lang_map: Dict[str, Any]) -> List[SignItem]:
        """Translate single word, falling back to fingerspelling."""
        clean_word = word.lower().strip()
        if not clean_word:
            return []

        if clean_word in lang_map:
            item = lang_map[clean_word]
            return [SignItem(
                type=item.get("type", "image"),
                path=self.normalize_media_path(item.get("path", "")),
                label=clean_word,
                tokenType="word",
                language=language,
                generated=item.get("generated", False)
            )]
        else:
            return self.fingerspell(clean_word, language, lang_map)

# Global singleton
translator_service = TranslatorService()
