"""
Tests for Phase 5: Continuous Gloss Recognition (Task B) and Sentence Translation (Task C).
"""

from pathlib import Path
import numpy as np
import pytest
import torch

from ml.datasets.base import NormalizedSample
from ml.evaluation.evaluator import ModelEvaluator
from ml.evaluation.metrics import compute_bleu, compute_chrf, compute_wer
from ml.models.continuous_seq2seq import ContinuousGlossRecognizer
from ml.models.translation_pipeline import (
    GlossToEnglishTranslator,
    SignTranslationPipeline,
)
from ml.preprocessing.vocabulary import Vocabulary
from ml.training.config import TrainingConfig
from ml.training.trainer import (
    ContinuousGlossDataset,
    ContinuousGlossTrainer,
)


def test_continuous_gloss_forward_and_ctc_decode():
    vocab = ["HELLO", "WORLD", "HOW", "YOU"]
    model = ContinuousGlossRecognizer(
        model_id="test_ctc_model",
        gloss_vocab=vocab,
        input_dim=48,
        hidden_dim=32,
        num_layers=1
    )

    batch_x = torch.randn(2, 40, 48)
    log_probs = model(batch_x)
    # CTCLoss expects (T, B, C)
    assert log_probs.shape == (40, 2, len(vocab) + 1)

    decoded = model.decode_ctc(log_probs)
    assert len(decoded) == 2
    assert isinstance(decoded[0], list)

    pred = model.predict(np.random.randn(30, 48).astype(np.float32))
    assert "gloss_sequence" in pred
    assert "confidence" in pred


def test_continuous_training_loop(tmp_path: Path):
    vocab_list = ["GOOD", "MORNING", "THANK", "YOU"]
    ctc_vocab = Vocabulary(vocab_list, ctc_mode=True)

    samples = [
        NormalizedSample(sample_id=f"c_{i}", video_path=f"v_{i}.mp4", task="continuous_gloss", gloss_sequence=["GOOD", "MORNING"], split="train")
        for i in range(8)
    ]
    val_samples = [
        NormalizedSample(sample_id=f"val_{i}", video_path=f"v_{i}.mp4", task="continuous_gloss", gloss_sequence=["THANK", "YOU"], split="val")
        for i in range(4)
    ]

    train_ds = ContinuousGlossDataset(samples, ctc_vocab, sequence_length=20, input_dim=36)
    val_ds = ContinuousGlossDataset(val_samples, ctc_vocab, sequence_length=20, input_dim=36)

    model = ContinuousGlossRecognizer(
        model_id="train_ctc_model",
        gloss_vocab=vocab_list,
        input_dim=36,
        hidden_dim=16,
        num_layers=1
    )

    config = TrainingConfig(
        task="continuous_gloss",
        model_id="train_ctc_model",
        dataset_adapter="how2sign",
        manifest_path=str(tmp_path / "manifest.json"),
        checkpoint_dir=str(tmp_path / "checkpoints"),
        input_dim=36,
        sequence_length=20,
        hidden_dim=16,
        num_layers=1,
        batch_size=4,
        epochs=2,
        learning_rate=0.01,
        device="cpu"
    )

    trainer = ContinuousGlossTrainer(config, model, train_ds, val_ds)
    result = trainer.train()

    assert result["status"] == "completed"
    assert result["total_epochs"] == 2
    best_ckpt = Path(result["checkpoint_path"])
    assert best_ckpt.exists()


def test_gloss_to_english_translator():
    translator = GlossToEnglishTranslator()

    # Direct phrase rule
    assert translator.translate_glosses(["GOOD", "MORNING"]) == "Good morning."
    assert translator.translate_glosses(["THANK", "YOU"]) == "Thank you."

    # Wh-question inversion
    res_q = translator.translate_glosses(["YOUR", "NAME", "WHAT"])
    assert res_q == "What is your name?"

    # Pronoun & copula synthesis
    res_pronoun = translator.translate_glosses(["ME", "HAPPY"])
    assert res_pronoun == "I am happy."


def test_translation_pipeline_e2e():
    vocab_list = ["GOOD", "MORNING", "WHAT", "YOUR", "NAME"]
    recognizer = ContinuousGlossRecognizer(
        model_id="rec_for_pipeline",
        gloss_vocab=vocab_list,
        input_dim=48,
        hidden_dim=32,
        num_layers=1
    )

    pipeline = SignTranslationPipeline(
        model_id="e2e_translation_pipeline",
        gloss_recognizer=recognizer
    )

    dummy_landmarks = np.random.randn(30, 48).astype(np.float32)
    output = pipeline.predict(dummy_landmarks)

    assert "english_translation" in output
    assert "gloss_sequence" in output
    assert output["task"] == "sentence_translation"


def test_sequence_metrics_wer_bleu_chrf():
    # WER test
    refs = [["HELLO", "WORLD"], ["HOW", "ARE", "YOU"]]
    hyps_exact = [["HELLO", "WORLD"], ["HOW", "ARE", "YOU"]]
    assert compute_wer(refs, hyps_exact) == 0.0

    hyps_sub = [["HELLO", "THERE"], ["HOW", "ARE", "YOU"]]
    # 1 substitution out of 5 words -> 0.20
    assert compute_wer(refs, hyps_sub) == 0.2

    # BLEU test
    ref_sentences = ["The cat sat on the mat."]
    hyp_sentences = ["The cat sat on the mat."]
    bleu_exact = compute_bleu(ref_sentences, hyp_sentences)
    assert bleu_exact > 90.0

    # chrF test
    chrf_exact = compute_chrf(ref_sentences, hyp_sentences)
    assert chrf_exact > 90.0
