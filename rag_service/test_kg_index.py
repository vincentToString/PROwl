"""Comprehensive test suite for Knowledge Graph Index."""
import asyncio
import sys
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import select
from database import init_db, AsyncSessionLocal, KGDocument, KGChunk, KGEntity, KGRelation
from indexes.knowledge_graph_index import KnowledgeGraphIndexEngine
from test_data import DOCUMENTS, TEST_QUERIES


class TestColors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{TestColors.HEADER}{TestColors.BOLD}{'=' * 80}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{text.center(80)}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{'=' * 80}{TestColors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{TestColors.OKGREEN}✓ {text}{TestColors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{TestColors.OKCYAN}ℹ {text}{TestColors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{TestColors.WARNING}⚠ {text}{TestColors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{TestColors.FAIL}✗ {text}{TestColors.ENDC}")


def print_section(text: str):
    """Print section header."""
    print(f"\n{TestColors.OKBLUE}{TestColors.BOLD}▶ {text}{TestColors.ENDC}")


def print_result(label: str, value: Any, indent: int = 0):
    """Print a labeled result."""
    spaces = "  " * indent
    print(f"{spaces}{TestColors.BOLD}{label}:{TestColors.ENDC} {value}")


async def test_database_initialization():
    """Test 1: Database initialization."""
    print_section("Test 1: Database Initialization")

    try:
        await init_db()
        print_success("Database tables created successfully")

        # Verify tables exist by querying them
        async with AsyncSessionLocal() as session:
            await session.execute(select(KGDocument).limit(1))
            await session.execute(select(KGChunk).limit(1))
            await session.execute(select(KGEntity).limit(1))
            await session.execute(select(KGRelation).limit(1))

        print_success("All tables are accessible")
        return True
    except Exception as e:
        print_error(f"Database initialization failed: {e}")
        return False


async def test_document_ingestion(kg_engine: KnowledgeGraphIndexEngine):
    """Test 2: Document ingestion."""
    print_section("Test 2: Document Ingestion")

    results = []

    async with AsyncSessionLocal() as session:
        for i, doc_data in enumerate(DOCUMENTS, 1):
            print_info(f"\nIngesting document {i}/{len(DOCUMENTS)}: {doc_data['title']}")

            try:
                start_time = datetime.utcnow()

                result = await kg_engine.ingest_document(
                    db=session,
                    document_id=doc_data['document_id'],
                    content=doc_data['content'],
                    title=doc_data['title'],
                    metadata=doc_data['metadata']
                )

                results.append(result)

                print_result("Document ID", result['document_id'], indent=1)
                print_result("Chunks Created", result['chunks_created'], indent=1)
                print_result("Entities Created", result['entities_created'], indent=1)
                print_result("Relations Created", result['relations_created'], indent=1)
                print_result("Duration", f"{result['duration_seconds']:.2f}s", indent=1)
                print_result("Status", result['status'], indent=1)

                if result['status'] == 'success':
                    print_success(f"Document '{doc_data['title']}' ingested successfully")
                else:
                    print_warning(f"Document ingestion completed with warnings")

            except Exception as e:
                print_error(f"Failed to ingest document: {e}")
                import traceback
                traceback.print_exc()

    # Print summary
    print_section("Ingestion Summary")
    total_chunks = sum(r['chunks_created'] for r in results)
    total_entities = sum(r['entities_created'] for r in results)
    total_relations = sum(r['relations_created'] for r in results)
    total_duration = sum(r['duration_seconds'] for r in results)

    print_result("Total Documents", len(results))
    print_result("Total Chunks", total_chunks)
    print_result("Total Entities", total_entities)
    print_result("Total Relations", total_relations)
    print_result("Total Time", f"{total_duration:.2f}s")
    if len(results) > 0:
        print_result("Average per Document", f"{total_duration/len(results):.2f}s")

    return len(results) == len(DOCUMENTS)


async def test_knowledge_graph_queries(kg_engine: KnowledgeGraphIndexEngine):
    """Test 3: Knowledge graph queries."""
    print_section("Test 3: Knowledge Graph Queries")

    query_failures = 0
    async with AsyncSessionLocal() as session:
        for i, query in enumerate(TEST_QUERIES[:5], 1):  # Test first 5 queries
            print_info(f"\nQuery {i}/{min(5, len(TEST_QUERIES))}: '{query}'")

            try:
                result = await kg_engine.query_knowledge_graph(
                    db=session,
                    query=query,
                    top_k=3,
                    include_relations=True
                )

                print_result("Chunks Found", len(result['chunks']), indent=1)
                print_result("Entities Found", len(result['entities']), indent=1)
                print_result("Relations Found", len(result['relations']), indent=1)

                # Show top chunk
                if result['chunks']:
                    top_chunk = result['chunks'][0]
                    print(f"  {TestColors.BOLD}Top Result:{TestColors.ENDC}")
                    print(f"    Score: {top_chunk['score']:.4f}")
                    print(f"    Preview: {top_chunk['content'][:150]}...")

                # Show entities
                if result['entities']:
                    print(f"  {TestColors.BOLD}Entities:{TestColors.ENDC}")
                    for entity in result['entities'][:3]:
                        print(f"    - {entity['text']} ({entity['type']})")

                # Show relations
                if result['relations']:
                    print(f"  {TestColors.BOLD}Relations:{TestColors.ENDC}")
                    for relation in result['relations'][:3]:
                        print(f"    - {relation['source']} --[{relation['type']}]--> {relation['target']}")

                print_success(f"Query executed successfully")

            except Exception as e:
                print_error(f"Query failed: {e}")
                query_failures += 1
                # Don't print full traceback for every error, just count them

    if query_failures > 0:
        print_warning(f"{query_failures}/{min(5, len(TEST_QUERIES))} queries failed")
        return False

    return True


async def test_document_graph_retrieval(kg_engine: KnowledgeGraphIndexEngine):
    """Test 4: Document graph retrieval."""
    print_section("Test 4: Document Graph Retrieval")

    async with AsyncSessionLocal() as session:
        for doc_data in DOCUMENTS[:2]:  # Test first 2 documents
            print_info(f"\nRetrieving graph for: {doc_data['title']}")

            try:
                result = await kg_engine.get_document_graph(
                    db=session,
                    document_id=doc_data['document_id']
                )

                if result:
                    print_result("Document ID", result['document_id'], indent=1)
                    print_result("Title", result['title'], indent=1)
                    print_result("Chunks", result['chunks_count'], indent=1)
                    print_result("Entities", len(result['entities']), indent=1)
                    print_result("Relations", len(result['relations']), indent=1)

                    # Show sample entities
                    if result['entities']:
                        print(f"  {TestColors.BOLD}Sample Entities:{TestColors.ENDC}")
                        for entity in result['entities'][:5]:
                            print(f"    - {entity['text']} ({entity['type']})")

                    # Show sample relations
                    if result['relations']:
                        print(f"  {TestColors.BOLD}Sample Relations:{TestColors.ENDC}")
                        for relation in result['relations'][:5]:
                            print(f"    - {relation['source']} --[{relation['type']}]--> {relation['target']}")

                    print_success(f"Document graph retrieved successfully")
                else:
                    print_error(f"Document not found")

            except Exception as e:
                print_error(f"Failed to retrieve document graph: {e}")
                import traceback
                traceback.print_exc()

    return True


async def test_database_state():
    """Test 5: Verify database state."""
    print_section("Test 5: Database State Verification")

    try:
        async with AsyncSessionLocal() as session:
            # Count documents
            doc_result = await session.execute(select(KGDocument))
            doc_count = len(doc_result.scalars().all())

            # Count chunks
            chunk_result = await session.execute(select(KGChunk))
            chunk_count = len(chunk_result.scalars().all())

            # Count entities
            entity_result = await session.execute(select(KGEntity))
            entity_count = len(entity_result.scalars().all())

            # Count relations
            relation_result = await session.execute(select(KGRelation))
            relation_count = len(relation_result.scalars().all())

            print_result("Documents in DB", doc_count)
            print_result("Chunks in DB", chunk_count)
            print_result("Entities in DB", entity_count)
            print_result("Relations in DB", relation_count)

            # Get entity type distribution
            entities = entity_result.scalars().all()
            entity_types = {}
            for entity in entities:
                entity_types[entity.entity_type] = entity_types.get(entity.entity_type, 0) + 1

            print(f"\n  {TestColors.BOLD}Entity Type Distribution:{TestColors.ENDC}")
            for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {entity_type}: {count}")

            # Get relation type distribution
            relations = relation_result.scalars().all()
            relation_types = {}
            for relation in relations:
                relation_types[relation.relation_type] = relation_types.get(relation.relation_type, 0) + 1

            print(f"\n  {TestColors.BOLD}Relation Type Distribution:{TestColors.ENDC}")
            for relation_type, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {relation_type}: {count}")

            print_success("Database state verified")
            return True

    except Exception as e:
        print_error(f"Failed to verify database state: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    print_header("Knowledge Graph Index - Comprehensive Test Suite")

    start_time = datetime.utcnow()
    test_results = []

    # Initialize engine
    print_info("Initializing Knowledge Graph Index Engine...")
    kg_engine = KnowledgeGraphIndexEngine()
    print_success("Engine initialized\n")

    # Test 1: Database initialization
    result = await test_database_initialization()
    test_results.append(("Database Initialization", result))

    if not result:
        print_error("\nDatabase initialization failed. Stopping tests.")
        return

    # Test 2: Document ingestion
    result = await test_document_ingestion(kg_engine)
    test_results.append(("Document Ingestion", result))

    # Test 3: Knowledge graph queries
    result = await test_knowledge_graph_queries(kg_engine)
    test_results.append(("Knowledge Graph Queries", result))

    # Test 4: Document graph retrieval
    result = await test_document_graph_retrieval(kg_engine)
    test_results.append(("Document Graph Retrieval", result))

    # Test 5: Database state
    result = await test_database_state()
    test_results.append(("Database State Verification", result))

    # Print final summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    print_header("Test Summary")

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print(f"\n{TestColors.BOLD}Results:{TestColors.ENDC}")
    print_result("Tests Passed", f"{passed}/{total}")
    print_result("Success Rate", f"{(passed/total)*100:.1f}%")
    print_result("Total Duration", f"{duration:.2f}s")

    if passed == total:
        print(f"\n{TestColors.OKGREEN}{TestColors.BOLD}All tests passed! ✓{TestColors.ENDC}\n")
    else:
        print(f"\n{TestColors.FAIL}{TestColors.BOLD}Some tests failed ✗{TestColors.ENDC}\n")


if __name__ == "__main__":
    print("\n")
    print(f"{TestColors.OKCYAN}Starting Knowledge Graph Index tests...{TestColors.ENDC}")
    print(f"{TestColors.WARNING}Note: Make sure PostgreSQL is running and accessible{TestColors.ENDC}")
    print(f"{TestColors.WARNING}Note: This will create/modify data in the database{TestColors.ENDC}\n")

    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print(f"\n{TestColors.WARNING}Tests interrupted by user{TestColors.ENDC}\n")
    except Exception as e:
        print(f"\n{TestColors.FAIL}Fatal error: {e}{TestColors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
