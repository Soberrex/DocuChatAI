import os
import sys
import time
from typing import Optional
from dotenv import load_dotenv

# Fix Windows console encoding for emoji output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

from src.page_index import get_page_index
from src.metrics import MetricsTracker

load_dotenv()


class HybridIndexer:
    """Document indexer using BM25 page index for retrieval"""

    def __init__(self):
        print(f"⚙️  Initializing Document Indexer (Lightweight)...")
        self.page_index = get_page_index()
        self.metrics = MetricsTracker()
        self._doc_count = 0
        print("✅ Indexer ready")

    def build_index(self, folder_path: str):
        """Index all supported files in a folder"""
        print(f"🚀 Scanning Dataset: {folder_path}")

        chunks = []
        count = 0

        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)

                # Process Python files
                if file.endswith(".py"):
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            code = f.read()
                            if len(code) > 50:
                                doc_text = f"FILE: {file}\nPATH: {full_path}\nCONTENT:\n{code[:5000]}"
                                chunks.append({
                                    'content': doc_text,
                                    'metadata': {'source_path': full_path}
                                })
                                count += 1
                                if count % 10 == 0:
                                    print(f"   🔹 Indexed {count} files...")
                    except Exception as e:
                        print(f"   ⚠️  Skipped {file}: {e}")

                # Process PDF files
                elif file.endswith(".pdf"):
                    try:
                        text = self._extract_pdf_text(full_path)
                        if len(text) > 100:
                            doc_text = f"FILE: {file}\nPATH: {full_path}\nCONTENT:\n{text[:5000]}"
                            chunks.append({
                                'content': doc_text,
                                'metadata': {'source_path': full_path}
                            })
                            count += 1
                            if count % 10 == 0:
                                print(f"   🔹 Indexed {count} files (including PDFs)...")
                    except Exception as e:
                        print(f"   ⚠️  Skipped PDF {file}: {e}")

                # Process TXT and MD files
                elif file.endswith((".txt", ".md")):
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                            if len(text) > 50:
                                doc_text = f"FILE: {file}\nPATH: {full_path}\nCONTENT:\n{text[:5000]}"
                                chunks.append({
                                    'content': doc_text,
                                    'metadata': {'source_path': full_path}
                                })
                                count += 1
                                if count % 10 == 0:
                                    print(f"   🔹 Indexed {count} files...")
                    except Exception as e:
                        print(f"   ⚠️  Skipped {file}: {e}")

        # Batch add to page index
        if chunks:
            doc_id = f"folder_{os.path.basename(folder_path)}"
            added = self.page_index.add_document_chunks(
                chunks=chunks,
                document_id=doc_id,
                filename=folder_path,
                file_type="folder"
            )
            self.page_index.persist()
            self._doc_count = added

        print(f"✅ Successfully indexed {count} files using Page Index.")

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF files"""
        text = ""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"   ⚠️  PyPDF2 failed, trying pdfplumber: {e}")
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e2:
                print(f"   ❌ Both PDF extractors failed: {e2}")
        return text

    def search(self, query: str, top_k: int = 10) -> Optional[str]:
        """Search for relevant documents using BM25"""
        start_time = time.time()
        print(f"🔍 Search: '{query}'")

        results = self.page_index.search(query=query, n_results=top_k)

        response_time = time.time() - start_time

        if not results:
            self.metrics.log_query(query, response_time, False, 0.0)
            print(f"   ⏱️  Response Time: {response_time*1000:.2f}ms")
            print(f"   ❌ No results found")
            return None

        best = results[0]
        best_file = best['metadata'].get('source_path', best['id'])
        top_score = best['score']

        self.metrics.log_query(query, response_time, True, top_score)

        print(f"   🎯 Winner: {best_file} (Score: {top_score:.4f})")
        print(f"   ⏱️  Response Time: {response_time*1000:.2f}ms")
        print(f"   📊 Confidence Score: {top_score:.4f}")

        return best_file

    @property
    def collection(self):
        """Compatibility property — returns a mock with count()"""
        class _MockCollection:
            def __init__(self, index):
                self._index = index
            def count(self):
                return len(self._index.page_index.chunks)
        return _MockCollection(self)