"""
Task C: Sentence-Level Sign Language Translation Pipeline.
Transforms unaligned continuous ASL signing streams into natural English sentences.
Implements a decoupled two-stage translation pipeline:
1. Video Landmark Stream -> Continuous Gloss Sequence (Task B)
2. ASL Gloss Sequence -> Grammatical English Sentence (Task C)
"""

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn

from ml.datasets.base import TaskType
from ml.models.base import BaseSignModel
from ml.models.continuous_seq2seq import ContinuousGlossRecognizer


class GlossToEnglishTranslator:
    """
    Translates ASL gloss sequences to fluent, grammatical English sentences.
    Accounts for ASL grammatical structures:
    - Wh-question inversion (e.g. [YOU, NAME, WHAT] -> "What is your name?")
    - Copula verb synthesis (e.g. [I, HAPPY] -> "I am happy")
    - Temporal / topic markers
    - Capitalization, contractions, and sentence boundary punctuation
    """

    def __init__(self, custom_lexicon: Optional[Dict[str, str]] = None):
        self.lexicon = custom_lexicon or {}

        # Common ASL idiom translations
        self.phrase_rules = {
            "GOOD MORNING": "Good morning.",
            "GOOD EVENING": "Good evening.",
            "HAVE GOOD DAY": "Have a good day.",
            "HOW YOU": "How are you?",
            "WHAT YOU DO": "What are you doing?",
            "WHAT YOUR NAME": "What is your name?",
            "YOUR NAME WHAT": "What is your name?",
            "NICE MEET YOU": "Nice to meet you.",
            "SEE YOU LATER": "See you later.",
            "THANK YOU": "Thank you."
        }

        # Pronoun mappings
        self.pronouns = {
            "ME": "I",
            "MY": "my",
            "YOU": "you",
            "YOUR": "your",
            "HE": "he",
            "SHE": "she",
            "THEY": "they",
            "WE": "we"
        }

    def translate_glosses(self, glosses: List[str]) -> str:
        """Translates a list of ASL gloss strings into an English sentence."""
        if not glosses:
            return ""

        clean_glosses = [g.strip().upper() for g in glosses if g.strip()]
        gloss_str = " ".join(clean_glosses)

        # 1. Direct phrase rule hit
        if gloss_str in self.phrase_rules:
            return self.phrase_rules[gloss_str]

        # 2. Wh-question detection (WHAT, WHERE, WHO, WHEN, WHY, HOW at end of ASL sequence)
        wh_words = {"WHAT", "WHERE", "WHO", "WHEN", "WHY", "HOW"}
        if len(clean_glosses) >= 2 and clean_glosses[-1] in wh_words:
            wh_word = clean_glosses[-1].capitalize()
            rest = clean_glosses[:-1]

            if rest == ["YOUR", "NAME"] or rest == ["YOU", "NAME"]:
                return f"{wh_word} is your name?"
            elif rest == ["YOU", "DOING"] or rest == ["YOU", "DO"]:
                return f"{wh_word} are you doing?"
            else:
                rest_str = " ".join([self.pronouns.get(w, w.lower()) for w in rest])
                return f"{wh_word} {rest_str}?"

        # 3. Copula insertion & grammar structuring
        translated_words: List[str] = []
        for i, g in enumerate(clean_glosses):
            word = self.pronouns.get(g, g.lower())
            translated_words.append(word)

        # Apply basic copula insertion if [I, adjective] or [you, adjective]
        if len(translated_words) >= 2:
            if translated_words[0] == "I" and translated_words[1] in ("fine", "good", "happy", "tired", "ready", "learning"):
                translated_words.insert(1, "am")
            elif translated_words[0] == "you" and translated_words[1] in ("fine", "good", "happy", "tired", "ready", "learning"):
                translated_words.insert(1, "are")

        # Join and punctuate
        sentence = " ".join(translated_words)
        sentence = sentence[0].upper() + sentence[1:] if sentence else ""

        if not sentence.endswith((".", "?", "!")):
            sentence += "."

        return sentence


class SignTranslationPipeline(BaseSignModel):
    """
    Task C: Full End-to-End ASL Video/Landmark to English Translation Pipeline.
    Combines continuous gloss recognition with gloss-to-English sequence translation.
    """

    def __init__(
        self,
        model_id: str,
        gloss_recognizer: ContinuousGlossRecognizer,
        translator: Optional[GlossToEnglishTranslator] = None
    ):
        super().__init__(model_id=model_id, task=TaskType.SENTENCE_TRANSLATION)
        self.gloss_recognizer = gloss_recognizer
        self.translator = translator or GlossToEnglishTranslator()

        self.metadata = {
            "model_id": model_id,
            "architecture": "GlossRecognizer_Translation_Pipeline",
            "task": TaskType.SENTENCE_TRANSLATION.value,
            "sub_model_id": gloss_recognizer.model_id,
            "gloss_classes": len(gloss_recognizer.gloss_vocab_raw)
        }

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass delegates to underlying continuous gloss recognizer."""
        return self.gloss_recognizer(x)

    def predict(self, sample_input: Union[np.ndarray, torch.Tensor]) -> Dict[str, Any]:
        """
        Inference executing full video landmark stream -> glosses -> English translation.
        """
        # 1. Recognize continuous glosses
        gloss_result = self.gloss_recognizer.predict(sample_input)
        gloss_sequence = gloss_result["gloss_sequence"]

        # 2. Translate glosses to grammatical English
        english_sentence = self.translator.translate_glosses(gloss_sequence)

        return {
            "english_translation": english_sentence,
            "gloss_sequence": gloss_sequence,
            "gloss_text": gloss_result.get("gloss_text", " ".join(gloss_sequence)),
            "confidence": gloss_result.get("confidence", 0.0),
            "frame_count": gloss_result.get("frame_count", 0),
            "task": TaskType.SENTENCE_TRANSLATION.value
        }

    @classmethod
    def load_checkpoint(cls, checkpoint_path: Path, device: str = "cpu") -> "SignTranslationPipeline":
        recognizer = ContinuousGlossRecognizer.load_checkpoint(checkpoint_path, device=device)
        return cls(
            model_id=f"{recognizer.model_id}_pipeline",
            gloss_recognizer=recognizer,
            translator=GlossToEnglishTranslator()
        )
