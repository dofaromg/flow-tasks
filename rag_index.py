#!/usr/bin/env python3
"""Build a simple TF-IDF index for files in a repository.

This script scans a repository directory for text files and saves a TF-IDF
index to an output directory. The resulting files (`vectorizer.pkl`,
`tfidf_matrix.npz`, and `paths.json`) can later be used to perform similarity
searches.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from scipy import sparse

SUPPORTED_SUFFIXES = (".py", ".md", ".txt")


def read_files(base_dir: Path) -> Tuple[List[str], List[str]]:
    """Collect text and file paths from base_dir.

    Parameters
    ----------
    base_dir: Path
        Directory to scan recursively.

    Returns
    -------
    Tuple[List[str], List[str]]
        Two lists: document contents and their corresponding paths.
    """

    docs: List[str] = []
    paths: List[str] = []

    for path in base_dir.rglob("*"):
        if path.suffix in SUPPORTED_SUFFIXES and path.is_file():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                # Skip files we can't read
                continue
            docs.append(text)
            paths.append(str(path))

    return docs, paths


def build_index(docs: List[str]) -> Tuple[TfidfVectorizer, sparse.csr_matrix]:
    """Build the TF-IDF vectorizer and document-term matrix."""
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(docs)
    return vectorizer, matrix


def main() -> None:
    parser = argparse.ArgumentParser(description="Build TF-IDF index for repository files.")
    parser.add_argument(
        "--repo-dir", default="./repo", help="Directory to scan for files (default: ./repo)"
    )
    parser.add_argument(
        "--index-dir", default="./index", help="Directory to store the index (default: ./index)"
    )
    args = parser.parse_args()

    repo_dir = Path(args.repo_dir)
    index_dir = Path(args.index_dir)

    if not repo_dir.exists():
        raise FileNotFoundError(f"Repository directory '{repo_dir}' does not exist")

    docs, paths = read_files(repo_dir)

    if not docs:
        raise RuntimeError(f"No documents found under '{repo_dir}' with supported extensions {SUPPORTED_SUFFIXES}")

    vectorizer, matrix = build_index(docs)

    index_dir.mkdir(parents=True, exist_ok=True)

    with open(index_dir / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    sparse.save_npz(index_dir / "tfidf_matrix.npz", matrix)

    with open(index_dir / "paths.json", "w", encoding="utf-8") as f:
        json.dump(paths, f, ensure_ascii=False, indent=2)

    print(f"Indexed {len(paths)} files into '{index_dir}'")


if __name__ == "__main__":
    main()
