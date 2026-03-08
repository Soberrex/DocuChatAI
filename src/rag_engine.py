"""
Enhanced RAG Engine with Source Tracking
Combines page index search with source citations
"""
from typing import List, Dict, Optional
from src.page_index import get_page_index
from src.llm import get_llm_client


class RAGEngine:
    """RAG pipeline with context retrieval and source tracking"""
    
    def __init__(self):
        self.page_index = get_page_index()
        self.llm_client = get_llm_client()
    
    async def process_query(
        self,
        query: str,
        session_id: str,
        conversation_history: Optional[List[Dict]] = None,
        top_k: int = 5,
        has_documents: bool = False
    ) -> Dict:
        """Process user query through RAG pipeline"""
        
        # Step 1: Retrieve relevant context
        context_chunks = self.page_index.search(
            query=query,
            n_results=top_k
        )
        
        if not context_chunks:
            if has_documents:
                # Documents exist but no relevant chunks found for this query
                # Return instant response without LLM call for speed
                greeting_words = {'hi', 'hii', 'hello', 'hey', 'hola', 'greetings', 'sup', 'yo', 'howdy'}
                query_lower = query.strip().rstrip('!?.').lower()
                
                if query_lower in greeting_words or len(query_lower) <= 3:
                    return {
                        'response': "Hey there! 👋 I have your documents loaded and ready to analyze. Ask me anything specific about the content — like summaries, key topics, definitions, or specific details!",
                        'sources': [],
                        'chart_data': None,
                        'confidence': 0.8,
                        'tokens_used': 0
                    }
                else:
                    return {
                        'response': f"I have your documents but couldn't find specific content matching \"{query[:50]}\". Try rephrasing or asking about specific topics, chapters, or terms from your uploaded documents.",
                        'sources': [],
                        'chart_data': None,
                        'confidence': 0.2,
                        'tokens_used': 0
                    }
            else:
                return {
                    'response': "I don't have any documents to answer from. Please upload some documents first.",
                    'sources': [],
                    'chart_data': None,
                    'confidence': 0.0,
                    'tokens_used': 0
                }
        
        # Step 2: Generate response with LLM
        llm_response = self.llm_client.generate_chat_response(
            query=query,
            context_chunks=context_chunks,
            conversation_history=conversation_history
        )
        
        # Step 3: Calculate confidence score
        confidence = self._calculate_confidence(context_chunks)
        
        return {
            'response': llm_response['response'],
            'sources': llm_response.get('sources', []),
            'chart_data': llm_response.get('chart_data'),
            'confidence': confidence,
            'tokens_used': llm_response.get('tokens_used', 0)
        }
    
    async def generate_document_summary(
        self,
        document_id: str,
        document_text: str,
        file_type: str
    ) -> Dict:
        """Generate comprehensive summary of document"""
        summary = self.llm_client.generate_summary(
            document_content=document_text,
            document_type=file_type
        )
        
        return {
            'summary': summary,
            'suggested_charts': summary.get('chart_suggestions', []),
            'document_id': document_id
        }
    
    def _calculate_confidence(self, context_chunks: List[Dict]) -> float:
        """Calculate confidence based on retrieval quality"""
        if not context_chunks:
            return 0.0
        
        scores = [chunk.get('score', 0) for chunk in context_chunks]
        avg_score = sum(scores) / len(scores) if scores else 0
        chunk_bonus = min(len(context_chunks) / 5, 1.0) * 0.2
        
        return round(min(avg_score + chunk_bonus, 1.0), 2)


# Global instance
rag_engine: Optional[RAGEngine] = None

def get_rag_engine() -> RAGEngine:
    """Get or create RAG engine singleton"""
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine
