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
import os
import pickle
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from scipy import sparse

SUPPORTED_SUFFIXES = (".py", ".md", ".txt")


def read_single_file(file_path: Path) -> Optional[Tuple[str, str]]:
    """Read a single file, returning content and path or None on failure.
    
    Parameters
    ----------
    file_path: Path
        File to read
        
    Returns
    -------
    Optional[Tuple[str, str]]
        Tuple of (content, path) or None if read fails
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return content, str(file_path)
    except Exception:
        return None


def read_files(base_dir: Path, max_workers: Optional[int] = None) -> Tuple[List[str], List[str]]:
    """Collect text and file paths from base_dir with parallel I/O.

    Parameters
    ----------
    base_dir: Path
        Directory to scan recursively.
    max_workers: Optional[int]
        Maximum number of parallel workers for file reading.
        If None, uses min(4, cpu_count) for optimal performance.

    Returns
    -------
    Tuple[List[str], List[str]]
        Two lists: document contents and their corresponding paths.
    """
    # Auto-scale workers based on CPU count, with a reasonable default
    if max_workers is None:
        cpu_count = os.cpu_count() or 1
        max_workers = min(4, cpu_count)
    
    # Use targeted glob patterns instead of filtering all files
    file_paths: List[Path] = []
    for suffix in SUPPORTED_SUFFIXES:
        file_paths.extend(base_dir.rglob(f"*{suffix}"))

    document_contents: List[str] = []
    result_paths: List[str] = []

    # Parallel file reading for better performance
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(read_single_file, file_paths)
        for result in results:
            if result is not None:
                content, path = result
                document_contents.append(content)
                result_paths.append(path)

    return document_contents, result_paths


def build_index(document_contents: List[str]) -> Tuple[TfidfVectorizer, sparse.csr_matrix]:
    """Build the TF-IDF vectorizer and document-term matrix."""
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(document_contents)
    return tfidf_vectorizer, tfidf_matrix


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

    document_contents, file_paths = read_files(repo_dir)

    if not document_contents:
        raise RuntimeError(f"No documents found under '{repo_dir}' with supported extensions {SUPPORTED_SUFFIXES}")

    tfidf_vectorizer, tfidf_matrix = build_index(document_contents)

    index_dir.mkdir(parents=True, exist_ok=True)

    with open(index_dir / "vectorizer.pkl", "wb") as vectorizer_file:
        pickle.dump(tfidf_vectorizer, vectorizer_file)

    sparse.save_npz(index_dir / "tfidf_matrix.npz", tfidf_matrix)

    with open(index_dir / "paths.json", "w", encoding="utf-8") as paths_file:
        json.dump(file_paths, paths_file, ensure_ascii=False, indent=2)

    print(f"Indexed {len(file_paths)} files into '{index_dir}'")


if __name__ == "__main__":
    main()
