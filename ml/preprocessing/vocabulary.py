"""
Vocabulary and Label Encoding for Isolated Signs and Sequence Glosses.
Handles mapping between string labels/tokens and integer IDs,
special tokens (<pad>, <unk>, <blank>, <sos>, <eos>), and JSON serialization.
"""

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union


class Vocabulary:
    """
    Bidirectional mapping between string tokens/labels and discrete integers.
    Supports special tokens for CTC (<blank>), padding (<pad>), and Seq2Seq (<sos>, <eos>).
    """

    def __init__(
        self,
        tokens: Optional[Iterable[str]] = None,
        include_special_tokens: bool = False,
        ctc_mode: bool = False
    ):
        self.include_special_tokens = include_special_tokens
        self.ctc_mode = ctc_mode
        self.token2idx: Dict[str, int] = {}
        self.idx2token: Dict[int, str] = {}

        # Reserved token indices
        if ctc_mode:
            # CTC convention: index 0 is blank
            self.add_token("<blank>")
        elif include_special_tokens:
            self.add_token("<pad>")
            self.add_token("<unk>")
            self.add_token("<sos>")
            self.add_token("<eos>")

        if tokens:
            for t in tokens:
                self.add_token(t)

    def add_token(self, token: str) -> int:
        clean = token.strip()
        if clean not in self.token2idx:
            new_id = len(self.token2idx)
            self.token2idx[clean] = new_id
            self.idx2token[new_id] = clean
            return new_id
        return self.token2idx[clean]

    def get_id(self, token: str, default_unk: bool = True) -> int:
        clean = token.strip()
        if clean in self.token2idx:
            return self.token2idx[clean]
        if default_unk and "<unk>" in self.token2idx:
            return self.token2idx["<unk>"]
        raise KeyError(f"Token '{token}' not present in vocabulary.")

    def get_token(self, idx: int) -> str:
        if idx in self.idx2token:
            return self.idx2token[idx]
        return "<unk>"

    def encode(self, tokens: List[str]) -> List[int]:
        return [self.get_id(t) for t in tokens]

    def decode(self, indices: List[int], remove_special: bool = True) -> List[str]:
        tokens = []
        for idx in indices:
            t = self.get_token(idx)
            if remove_special and t in ("<pad>", "<unk>", "<sos>", "<eos>", "<blank>"):
                continue
            tokens.append(t)
        return tokens

    @property
    def pad_id(self) -> Optional[int]:
        return self.token2idx.get("<pad>")

    @property
    def unk_id(self) -> Optional[int]:
        return self.token2idx.get("<unk>")

    @property
    def blank_id(self) -> Optional[int]:
        return self.token2idx.get("<blank>")

    def __len__(self) -> int:
        return len(self.token2idx)

    def save(self, file_path: Union[str, Path]) -> None:
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "token2idx": self.token2idx,
            "include_special_tokens": self.include_special_tokens,
            "ctc_mode": self.ctc_mode
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "Vocabulary":
        p = Path(file_path)
        with open(p, "r", encoding="utf-8") as f:
            payload = json.load(f)

        vocab = cls(
            include_special_tokens=payload.get("include_special_tokens", False),
            ctc_mode=payload.get("ctc_mode", False)
        )
        vocab.token2idx = payload["token2idx"]
        vocab.idx2token = {int(v): k for k, v in payload["token2idx"].items()}
        return vocab
