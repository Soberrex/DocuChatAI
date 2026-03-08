"""
OpenAI / OpenRouter LLM Integration Module
Handles all interactions with LLM API for chat, summaries, and embeddings
"""
import os
import json
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """Wrapper for OpenAI-compatible API with token counting and error handling"""
    
    def __init__(self):
        # Try OpenRouter first, then OpenAI
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = None
        self.model = "gpt-4o-mini"
        
        if not self.api_key:
            print("⚠️ No LLM API key found. Chat responses will be limited.")
            self.client = None
            return
        
        # Detect which API to use
        if os.getenv("OPENROUTER_API_KEY"):
            self.base_url = "https://openrouter.ai/api/v1"
            self.model = "openai/gpt-4o-mini"  # OpenRouter model path
            print("✅ Using OpenRouter API")
        else:
            self.base_url = None  # Default OpenAI
            print("✅ Using OpenAI API")
        
        try:
            from openai import OpenAI
            if self.base_url:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=30.0)
            else:
                self.client = OpenAI(api_key=self.api_key, timeout=30.0)
        except ImportError:
            print("⚠️ openai package not installed. Running without LLM.")
            self.client = None
    
    def count_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        """Count tokens in text for cost estimation"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4
    
    def generate_summary(
        self, 
        document_content: str, 
        document_type: str = "general"
    ) -> Dict[str, Any]:
        """Generate comprehensive summary of document"""
        if not self.client:
            return {
                "executive_summary": "LLM not available. Document uploaded and indexed for search.",
                "key_findings": [],
                "metrics": {},
                "data_entities": [],
                "chart_suggestions": []
            }
        
        prompt = f"""Analyze this {document_type} document and provide a structured summary.

Document Content:
{document_content[:8000]}

Please provide:
1. Executive Summary (3-5 sentences)
2. Key Findings (5-7 bullet points)
3. Important Metrics (numbers, percentages, dates)
4. Data Entities suitable for visualization
5. Suggested Chart Types

Format your response as JSON with keys: executive_summary, key_findings, metrics, data_entities, chart_suggestions"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                # Strip markdown code fences if present
                if content.startswith("```"):
                    content = content.split("\n", 1)[1]
                    content = content.rsplit("```", 1)[0]
                return json.loads(content)
            except (json.JSONDecodeError, IndexError):
                return {
                    "executive_summary": content[:500] if content else "Summary generation failed",
                    "key_findings": [],
                    "metrics": {},
                    "data_entities": [],
                    "chart_suggestions": []
                }
                
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {
                "executive_summary": f"Summary generation error: {str(e)[:100]}",
                "key_findings": [],
                "metrics": {},
                "error": str(e)
            }
    
    def generate_chat_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate context-aware chat response with source citations"""
        if not self.client:
            return {
                "response": "LLM is not configured. Please set OPENROUTER_API_KEY or OPENAI_API_KEY.",
                "sources": [],
                "chart_data": None,
                "tokens_used": 0
            }
        
        # Format context with sources (limit chunks and truncate for speed)
        context_text = "\n\n".join([
            f"[Source: {chunk['metadata'].get('filename', 'Unknown')}, "
            f"Page: {chunk['metadata'].get('page', 'N/A')}]\n{chunk['content'][:800]}"
            for chunk in context_chunks[:3]
        ])
        
        prompt = f"""Answer the user's question using ONLY the provided context from their documents.

Context from Documents:
{context_text}

User Question: {query}

Instructions:
1. Provide a comprehensive answer using ONLY information from the context
2. Cite sources using [Document: filename] format
3. Include specific numbers, dates, and facts from the context
4. If the information is not in the context, clearly state that

Answer:"""

        messages = [
            {"role": "system", "content": "You are a helpful AI assistant that answers questions based on provided documents. Always cite your sources."}
        ]
        
        if conversation_history:
            messages.extend(conversation_history[-6:])
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=600
            )
            
            content = response.choices[0].message.content
            
            sources = [
                {
                    "document": chunk['metadata'].get('filename', 'Unknown'),
                    "page": chunk['metadata'].get('page', 'N/A'),
                    "snippet": chunk['content'][:200],
                    "relevance_score": chunk.get('score', 0.0)
                }
                for chunk in context_chunks[:3]
            ]
            
            # Chart detection (skip extraction LLM call for speed)
            chart_data = None
            
            return {
                "response": content,
                "sources": sources,
                "chart_data": chart_data,
                "tokens_used": self.count_tokens(prompt + (content or ""))
            }
            
        except Exception as e:
            print(f"Error generating chat response: {e}")
            return {
                "response": f"I encountered an error processing your question: {str(e)[:200]}",
                "sources": [],
                "chart_data": None,
                "error": str(e)
            }
    
    def _detect_chart_need(self, query: str, response: str) -> bool:
        """Detect if a chart would be useful"""
        chart_keywords = [
            "compare", "comparison", "vs", "versus", "difference",
            "trend", "over time", "growth", "change",
            "distribution", "breakdown", "percentage",
            "top", "bottom", "highest", "lowest"
        ]
        text = (query + " " + (response or "")).lower()
        return any(kw in text for kw in chart_keywords)
    
    def _extract_chart_data(
        self, 
        response: str, 
        context_chunks: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Extract structured data for chart generation"""
        if not self.client:
            return None
            
        prompt = f"""From this response, extract data suitable for a chart.

Response: {response[:1000]}

Provide a JSON object with:
- chart_type: "bar", "line", "pie", or "scatter"
- title: Chart title
- labels: Array of labels
- values: Array of corresponding values
- unit: Unit of measurement

If no clear data for charting, return {{"chart_type": null}}"""

        try:
            result = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract chart data as JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = result.choices[0].message.content
            if content and content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(content)
            return data if data.get("chart_type") else None
            
        except Exception as e:
            print(f"Error extracting chart data: {e}")
            return None


# Global instance
llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton"""
    global llm_client
    if llm_client is None:
        llm_client = LLMClient()
    return llm_client
