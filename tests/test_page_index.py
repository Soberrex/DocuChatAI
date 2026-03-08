"""
Unit tests for PageIndex — BM25-based document retrieval
"""
import pytest
import os
import json
import tempfile
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.page_index import PageIndex


@pytest.fixture
def temp_index():
    """Create a PageIndex with a temporary persist path"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_index.json")
        index = PageIndex(persist_path=path)
        yield index


@pytest.fixture
def populated_index(temp_index):
    """A PageIndex with sample financial document chunks"""
    chunks = [
        {
            'content': 'Total revenue for Q1 2024 was $28 lakh. Expenses were $20.5 lakh.',
            'metadata': {'page': 1}
        },
        {
            'content': 'Q2 revenue increased to $30 lakh. Marketing expenses rose by 15%.',
            'metadata': {'page': 2}
        },
        {
            'content': 'The company hired 12 new employees in Q3. Total headcount reached 150.',
            'metadata': {'page': 3}
        },
        {
            'content': 'Annual profit margin was 25.6%. Operations cost was the largest category.',
            'metadata': {'page': 4}
        },
        {
            'content': 'Customer acquisition cost dropped from $50 to $35 in Q4.',
            'metadata': {'page': 5}
        },
    ]

    temp_index.add_document_chunks(
        chunks=chunks,
        document_id='doc_financial_2024',
        filename='quarterly_report.xlsx',
        file_type='xlsx'
    )
    return temp_index


class TestPageIndexInit:
    """Test PageIndex initialization"""

    def test_empty_init(self, temp_index):
        """Test that a new index starts empty"""
        assert len(temp_index.chunks) == 0
        assert temp_index.search("anything") == []

    def test_init_prints_message(self, capsys, temp_index):
        """Test that init prints confirmation"""
        captured = capsys.readouterr()
        assert "Page Index initialized" in captured.out


class TestAddChunks:
    """Test document chunk adding"""

    def test_add_chunks(self, temp_index):
        """Test adding chunks returns correct count"""
        chunks = [
            {'content': 'Hello world', 'metadata': {}},
            {'content': 'Goodbye world', 'metadata': {}},
        ]
        count = temp_index.add_document_chunks(chunks, 'doc1', 'test.txt', 'txt')
        assert count == 2
        assert len(temp_index.chunks) == 2

    def test_add_empty_chunks(self, temp_index):
        """Test adding empty list returns 0"""
        count = temp_index.add_document_chunks([], 'doc1', 'test.txt', 'txt')
        assert count == 0

    def test_chunk_metadata_stored(self, temp_index):
        """Test that metadata is correctly stored"""
        chunks = [{'content': 'Test content', 'metadata': {'page': 5, 'section': 'intro'}}]
        temp_index.add_document_chunks(chunks, 'doc1', 'report.pdf', 'pdf')

        chunk_data = list(temp_index.chunks.values())[0]
        assert chunk_data['metadata']['document_id'] == 'doc1'
        assert chunk_data['metadata']['filename'] == 'report.pdf'
        assert chunk_data['metadata']['page'] == 5

    def test_multiple_documents(self, temp_index):
        """Test adding chunks from different documents"""
        temp_index.add_document_chunks(
            [{'content': 'Doc 1 content', 'metadata': {}}],
            'doc1', 'a.txt', 'txt'
        )
        temp_index.add_document_chunks(
            [{'content': 'Doc 2 content', 'metadata': {}}],
            'doc2', 'b.txt', 'txt'
        )
        assert len(temp_index.chunks) == 2
        assert len(temp_index.doc_chunks) == 2


class TestSearch:
    """Test BM25 search functionality"""

    def test_basic_search(self, populated_index):
        """Test that search returns results for matching query"""
        results = populated_index.search("revenue Q1 2024")
        assert len(results) > 0
        assert results[0]['score'] > 0

    def test_search_relevance(self, populated_index):
        """Test that most relevant result ranks first"""
        results = populated_index.search("revenue Q1")
        # Q1 revenue chunk should rank highest
        assert 'revenue' in results[0]['content'].lower()
        assert 'Q1' in results[0]['content']

    def test_search_no_match(self, populated_index):
        """Test search with completely unrelated query"""
        results = populated_index.search("quantum physics black holes")
        # BM25 may return 0 results for completely unrelated terms
        assert isinstance(results, list)

    def test_search_n_results(self, populated_index):
        """Test that n_results limits output"""
        results = populated_index.search("revenue", n_results=2)
        assert len(results) <= 2

    def test_search_empty_query(self, populated_index):
        """Test search with empty query"""
        results = populated_index.search("")
        assert results == []

    def test_search_by_document_id(self, populated_index):
        """Test filtering search by document_id"""
        # Add a second document
        populated_index.add_document_chunks(
            [{'content': 'Revenue from product A', 'metadata': {}}],
            'doc_other', 'other.txt', 'txt'
        )

        results = populated_index.search("revenue", document_id='doc_financial_2024')
        for r in results:
            assert r['metadata']['document_id'] == 'doc_financial_2024'

    def test_search_score_normalization(self, populated_index):
        """Test that scores are normalized to 0-1"""
        results = populated_index.search("revenue profit margin")
        for r in results:
            assert 0 <= r['score'] <= 1

    def test_search_result_structure(self, populated_index):
        """Test that each result has required fields"""
        results = populated_index.search("revenue")
        assert len(results) > 0
        result = results[0]
        assert 'id' in result
        assert 'content' in result
        assert 'metadata' in result
        assert 'score' in result


class TestDeletion:
    """Test document and session deletion"""

    def test_delete_document(self, populated_index):
        """Test deleting a document removes all its chunks"""
        initial_count = len(populated_index.chunks)
        assert initial_count > 0

        success = populated_index.delete_document('doc_financial_2024')
        assert success is True
        assert len(populated_index.chunks) == 0

    def test_delete_nonexistent_document(self, populated_index):
        """Test deleting non-existent document returns False"""
        success = populated_index.delete_document('nonexistent_doc')
        assert success is False

    def test_delete_session(self, temp_index):
        """Test deleting by session scans metadata"""
        chunks = [{'content': 'Session data', 'metadata': {'session_id': 'sess_123'}}]
        temp_index.add_document_chunks(chunks, 'doc1', 'test.txt', 'txt')

        # Manually add session_id to metadata (simulating upload flow)
        for cdata in temp_index.chunks.values():
            cdata['metadata']['session_id'] = 'sess_123'

        success = temp_index.delete_session('sess_123')
        assert success is True
        assert len(temp_index.chunks) == 0

    def test_get_document_stats(self, populated_index):
        """Test getting document statistics"""
        stats = populated_index.get_document_stats('doc_financial_2024')
        assert stats['chunk_count'] == 5
        assert stats['document_id'] == 'doc_financial_2024'


class TestPersistence:
    """Test save/load functionality"""

    def test_persist_and_load(self, temp_index):
        """Test that index survives persist + reload"""
        chunks = [
            {'content': 'Persistent content alpha', 'metadata': {'key': 'val'}},
            {'content': 'Persistent content beta', 'metadata': {}},
        ]
        temp_index.add_document_chunks(chunks, 'persist_doc', 'test.txt', 'txt')
        temp_index.persist()

        # Create new index from same path
        reloaded = PageIndex(persist_path=temp_index.persist_path)
        assert len(reloaded.chunks) == 2

        # Verify search still works after reload
        results = reloaded.search("persistent alpha")
        assert len(results) > 0
        assert 'alpha' in results[0]['content'].lower()

    def test_persist_creates_directory(self):
        """Test that persist creates parent directory if missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "dir", "index.json")
            index = PageIndex(persist_path=path)
            index.add_document_chunks(
                [{'content': 'Test', 'metadata': {}}], 'doc1', 'f.txt', 'txt'
            )
            index.persist()
            assert os.path.exists(path)

    def test_load_corrupted_file(self):
        """Test graceful handling of corrupted index file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bad.json")
            with open(path, 'w') as f:
                f.write("not valid json {{{")

            index = PageIndex(persist_path=path)
            assert len(index.chunks) == 0  # Should recover gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
