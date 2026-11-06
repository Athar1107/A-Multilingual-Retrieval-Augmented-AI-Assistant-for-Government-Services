"""Deterministic stratified train/test split for threshold calibration.

Splits eval_dataset_en.csv and eval_dataset_kok.csv into:
  - Calibration set (approx 60%)
  - Held-out test set (approx 40%)
Stratified by language and corpus membership (in-corpus vs out-of-corpus).
Fixed random seed ensures reproducibility.
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

EVAL_DIR = Path(__file__).parent
EN_CSV = EVAL_DIR / "eval_dataset_en.csv"
KOK_CSV = EVAL_DIR / "eval_dataset_kok.csv"
SPLIT_FILE = EVAL_DIR / "dataset_split.json"
SEED = 42


def make_split(seed: int = SEED) -> dict[str, dict[str, list[str]]]:
    rng = random.Random(seed)

    def split_items(items: list[str], frac: float = 0.6) -> tuple[list[str], list[str]]:
        shuffled = sorted(items)  # start from deterministic order
        rng.shuffle(shuffled)
        k = int(round(len(shuffled) * frac))
        return sorted(shuffled[:k]), sorted(shuffled[k:])

    # English
    en_in: list[str] = []
    en_ooc: list[str] = []
    with open(EN_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["category"] == "out_of_corpus":
                en_ooc.append(r["id"])
            else:
                en_in.append(r["id"])

    en_in_cal, en_in_test = split_items(en_in, 0.60)
    en_ooc_cal, en_ooc_test = split_items(en_ooc, 0.60)

    # Konkani
    kok_in: list[str] = []
    kok_ooc: list[str] = []
    with open(KOK_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["category"] == "out_of_corpus":
                kok_ooc.append(r["id"])
            else:
                kok_in.append(r["id"])

    kok_in_cal, kok_in_test = split_items(kok_in, 0.60)
    kok_ooc_cal, kok_ooc_test = split_items(kok_ooc, 0.60)

    split = {
        "metadata": {
            "seed": seed,
            "calibration_fraction": 0.60,
            "held_out_fraction": 0.40,
        },
        "en": {
            "calibration_ids": sorted(en_in_cal + en_ooc_cal),
            "held_out_ids": sorted(en_in_test + en_ooc_test),
            "in_corpus_calibration": en_in_cal,
            "in_corpus_held_out": en_in_test,
            "ooc_calibration": en_ooc_cal,
            "ooc_held_out": en_ooc_test,
        },
        "kok": {
            "calibration_ids": sorted(kok_in_cal + kok_ooc_cal),
            "held_out_ids": sorted(kok_in_test + kok_ooc_test),
            "in_corpus_calibration": kok_in_cal,
            "in_corpus_held_out": kok_in_test,
            "ooc_calibration": kok_ooc_cal,
            "ooc_held_out": kok_ooc_test,
        },
    }
    return split


def main() -> None:
    split = make_split()
    SPLIT_FILE.write_text(json.dumps(split, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Stratified dataset split generated and written to {SPLIT_FILE}")
    print(f"EN: {len(split['en']['calibration_ids'])} calibration, {len(split['en']['held_out_ids'])} test")
    print(f"KOK: {len(split['kok']['calibration_ids'])} calibration, {len(split['kok']['held_out_ids'])} test")


if __name__ == "__main__":
    main()

