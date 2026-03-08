"""
Page Index — Lightweight BM25-based document retrieval
Replaces ChromaDB vector database with zero external ML model dependencies.
Uses BM25Okapi for sparse retrieval + TF-IDF boosting.
"""
import os
import sys
import json
import re
import math
from typing import List, Dict, Optional
from collections import Counter, defaultdict

# Fix Windows console encoding for emoji output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass


class PageIndex:
    """BM25 + TF-IDF page index for document chunk retrieval"""

    def __init__(self, persist_path: str = "data/page_index.json"):
        self.persist_path = persist_path
        self.chunks: Dict[str, Dict] = {}       # chunk_id -> {content, metadata}
        self.doc_chunks: Dict[str, List[str]] = defaultdict(list)  # doc_id -> [chunk_ids]
        self.idf: Dict[str, float] = {}
        self._dirty = False
        self._load()
        print(f"✅ Page Index initialized ({len(self.chunks)} existing chunks)")

    # ── Tokenization ────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing"""
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9_]+\b', text)
        return tokens

    # ── Index Management ────────────────────────────────

    def add_document_chunks(
        self,
        chunks: List[Dict],
        document_id: str,
        filename: str,
        file_type: str
    ) -> int:
        """Add document chunks to the index"""
        if not chunks:
            return 0

        added = 0
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"

            metadata = {
                'document_id': document_id,
                'filename': filename,
                'file_type': file_type,
                'chunk_index': i,
            }
            # Add simple metadata from chunk
            for k, v in chunk.get('metadata', {}).items():
                if isinstance(v, (str, int, float, bool)):
                    metadata[k] = v

            self.chunks[chunk_id] = {
                'content': chunk['content'],
                'metadata': metadata,
                'tokens': self._tokenize(chunk['content']),
            }
            self.doc_chunks[document_id].append(chunk_id)
            added += 1

        # Rebuild IDF after adding new documents
        self._rebuild_idf()
        self._dirty = True
        return added

    def _rebuild_idf(self):
        """Rebuild inverse document frequency scores"""
        n_docs = len(self.chunks)
        if n_docs == 0:
            self.idf = {}
            return

        doc_freq: Counter = Counter()
        for chunk_data in self.chunks.values():
            unique_tokens = set(chunk_data['tokens'])
            for token in unique_tokens:
                doc_freq[token] += 1

        self.idf = {
            token: math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1)
            for token, freq in doc_freq.items()
        }

    # ── Search ──────────────────────────────────────────

    def search(
        self,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """Search for relevant chunks using BM25 scoring"""
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # BM25 parameters
        k1 = 1.5
        b = 0.75

        # Calculate average document length
        all_lengths = [len(c['tokens']) for c in self.chunks.values()]
        avg_dl = sum(all_lengths) / len(all_lengths) if all_lengths else 1

        scores: List[tuple] = []

        for chunk_id, chunk_data in self.chunks.items():
            # Filter by document_id if specified
            if document_id and chunk_data['metadata'].get('document_id') != document_id:
                continue

            doc_tokens = chunk_data['tokens']
            dl = len(doc_tokens)
            token_freq = Counter(doc_tokens)

            score = 0.0
            for qt in query_tokens:
                tf = token_freq.get(qt, 0)
                idf = self.idf.get(qt, 0)
                # BM25 scoring formula
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * dl / avg_dl)
                score += idf * (numerator / denominator) if denominator > 0 else 0

            if score > 0:
                scores.append((chunk_id, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Normalize scores to 0-1 range
        max_score = scores[0][1] if scores else 1.0

        results = []
        for chunk_id, score in scores[:n_results]:
            chunk_data = self.chunks[chunk_id]
            results.append({
                'id': chunk_id,
                'content': chunk_data['content'],
                'metadata': chunk_data['metadata'],
                'score': round(score / max_score, 4) if max_score > 0 else 0,
            })

        return results

    # ── Deletion ────────────────────────────────────────

    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document"""
        chunk_ids = self.doc_chunks.pop(document_id, [])
        if not chunk_ids:
            return False

        for cid in chunk_ids:
            self.chunks.pop(cid, None)

        self._rebuild_idf()
        self._dirty = True
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete all chunks for a session (by scanning metadata)"""
        doc_ids_to_remove = set()
        for chunk_data in self.chunks.values():
            if chunk_data['metadata'].get('session_id') == session_id:
                doc_ids_to_remove.add(chunk_data['metadata'].get('document_id'))

        if not doc_ids_to_remove:
            return False

        for doc_id in doc_ids_to_remove:
            self.delete_document(doc_id)

        return True

    def get_document_stats(self, document_id: str) -> Dict:
        """Get statistics for a document"""
        chunk_ids = self.doc_chunks.get(document_id, [])
        return {
            'chunk_count': len(chunk_ids),
            'document_id': document_id,
        }

    # ── Persistence ─────────────────────────────────────

    def persist(self):
        """Save index to disk"""
        if not self._dirty:
            return

        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)

        # Serialize without tokens (they are rebuilt on load)
        data = {
            'chunks': {
                cid: {
                    'content': c['content'],
                    'metadata': c['metadata'],
                }
                for cid, c in self.chunks.items()
            },
            'doc_chunks': dict(self.doc_chunks),
        }

        with open(self.persist_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        self._dirty = False

    def _load(self):
        """Load index from disk"""
        if not os.path.exists(self.persist_path):
            return

        try:
            with open(self.persist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for cid, c in data.get('chunks', {}).items():
                self.chunks[cid] = {
                    'content': c['content'],
                    'metadata': c['metadata'],
                    'tokens': self._tokenize(c['content']),
                }

            self.doc_chunks = defaultdict(list, data.get('doc_chunks', {}))
            self._rebuild_idf()

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Failed to load page index: {e}")
            self.chunks = {}
            self.doc_chunks = defaultdict(list)


# ── Global Singleton ────────────────────────────────────

_page_index: Optional[PageIndex] = None


def get_page_index() -> PageIndex:
    """Get or create page index singleton"""
    global _page_index
    if _page_index is None:
        _page_index = PageIndex()
    return _page_index
