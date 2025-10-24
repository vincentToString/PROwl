"""Test client for the RAG service Knowledge Graph Index."""
import requests
import json
from typing import Dict, Any


class RAGClient:
    """Client for interacting with the RAG service."""

    def __init__(self, base_url: str = "http://localhost:8002"):
        """Initialize client."""
        self.base_url = base_url

    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def ingest_document(
        self,
        document_id: str,
        content: str,
        title: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Ingest a document."""
        payload = {
            "document_id": document_id,
            "content": content,
            "title": title,
            "metadata": metadata or {}
        }

        response = requests.post(
            f"{self.base_url}/api/v1/kg-index/ingest",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def query(
        self,
        query: str,
        top_k: int = 5,
        include_relations: bool = True
    ) -> Dict[str, Any]:
        """Query the knowledge graph."""
        payload = {
            "query": query,
            "top_k": top_k,
            "include_relations": include_relations
        }

        response = requests.post(
            f"{self.base_url}/api/v1/kg-index/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_document_graph(self, document_id: str) -> Dict[str, Any]:
        """Get document graph."""
        response = requests.get(
            f"{self.base_url}/api/v1/kg-index/document/{document_id}"
        )
        response.raise_for_status()
        return response.json()


def print_json(data: Dict[str, Any], title: str = None):
    """Pretty print JSON data."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"{title}")
        print('=' * 60)
    print(json.dumps(data, indent=2))


def main():
    """Run test examples."""
    client = RAGClient()

    # 1. Health check
    print("Testing RAG Service...")
    health = client.health_check()
    print_json(health, "Health Check")

    # 2. Ingest a sample document
    sample_doc = """
    Artificial Intelligence (AI) is transforming the modern world.
    Machine Learning, a subset of AI, enables computers to learn from data
    without explicit programming. Deep Learning, which uses neural networks,
    has revolutionized computer vision and natural language processing.

    Companies like Google, Microsoft, and OpenAI are leading AI research.
    They develop advanced models like GPT and BERT for language understanding.
    AI applications include autonomous vehicles, medical diagnosis, and
    recommendation systems.

    The future of AI involves solving challenges in explainability, ethics,
    and ensuring AI systems are safe and beneficial for humanity.
    """

    print("\n\nIngesting sample document...")
    ingest_result = client.ingest_document(
        document_id="ai-overview-001",
        content=sample_doc,
        title="Introduction to AI and Machine Learning",
        metadata={
            "category": "technology",
            "tags": ["AI", "ML", "Deep Learning"],
            "author": "Test User"
        }
    )
    print_json(ingest_result, "Ingestion Result")

    # 3. Query the knowledge graph
    print("\n\nQuerying knowledge graph...")
    query_result = client.query(
        query="What is machine learning?",
        top_k=3,
        include_relations=True
    )
    print_json(query_result, "Query Result: 'What is machine learning?'")

    # 4. Get document graph
    print("\n\nFetching document graph...")
    doc_graph = client.get_document_graph("ai-overview-001")
    print_json(doc_graph, "Document Graph")

    # 5. Another query
    print("\n\nQuerying for companies...")
    query_result2 = client.query(
        query="Which companies work on AI?",
        top_k=3,
        include_relations=True
    )
    print_json(query_result2, "Query Result: 'Which companies work on AI?'")

    print("\n\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to RAG service.")
        print("Make sure the service is running at http://localhost:8002")
    except Exception as e:
        print(f"Error: {e}")
