"""
Integration tests for RAG database management functionality
"""

from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_rag_stats_endpoint(async_client: AsyncClient):
    """Test RAG stats endpoint"""
    response = await async_client.get("/api/v2/rag/stats")
    assert response.status_code == 200

    data = response.json()
    assert "status_code" in data
    assert data["status_code"] == 200
    assert "data" in data

    stats = data["data"]
    assert "total_documents" in stats
    assert "total_chunks" in stats
    assert "total_embeddings" in stats
    assert "storage_size_mb" in stats
    assert "last_updated" in stats
    assert "vector_store_type" in stats
    assert "embedding_model" in stats


@pytest.mark.asyncio
async def test_rag_documents_list_endpoint(async_client: AsyncClient):
    """Test RAG documents list endpoint"""
    response = await async_client.get("/api/v2/rag/documents")
    assert response.status_code == 200

    # Should return a list (even if empty)
    documents = response.json()
    assert isinstance(documents, list)


@pytest.mark.asyncio
async def test_rag_directories_list_endpoint(async_client: AsyncClient):
    """Test RAG directories list endpoint"""
    response = await async_client.get("/api/v2/rag/directories")
    assert response.status_code == 200

    # Should return a list (even if empty)
    directories = response.json()
    assert isinstance(directories, list)


@pytest.mark.asyncio
async def test_rag_search_endpoint(async_client: AsyncClient):
    """Test RAG search endpoint"""
    response = await async_client.get("/api/v2/rag/search?query=test&k=5")
    assert response.status_code == 200

    data = response.json()
    assert "status_code" in data
    assert data["status_code"] == 200
    assert "data" in data


@pytest.mark.asyncio
async def test_rag_sync_database_endpoint(async_client: AsyncClient):
    """Test RAG database sync endpoint"""
    # Test with valid sync type
    response = await async_client.post("/api/v2/rag/sync-database?sync_type=all")
    assert response.status_code == 200

    data = response.json()
    assert "status_code" in data
    assert data["status_code"] == 200
    assert "data" in data


@pytest.mark.asyncio
async def test_rag_sync_database_invalid_type(async_client: AsyncClient):
    """Test RAG database sync with invalid sync type"""
    response = await async_client.post("/api/v2/rag/sync-database?sync_type=invalid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_rag_create_directory_endpoint(async_client: AsyncClient):
    """Test RAG create directory endpoint"""
    response = await async_client.post(
        "/api/v2/rag/create-directory?directory_path=test_directory"
    )
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "test_directory" in data["message"]


@pytest.mark.asyncio
async def test_rag_delete_directory_endpoint(async_client: AsyncClient):
    """Test RAG delete directory endpoint"""
    # First create a directory
    await async_client.post(
        "/api/v2/rag/create-directory?directory_path=test_delete_directory"
    )

    # Then delete it
    response = await async_client.delete(
        "/api/v2/rag/directories/test_delete_directory"
    )
    assert response.status_code == 200

    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_rag_directory_stats_endpoint(async_client: AsyncClient):
    """Test RAG directory stats endpoint"""
    # Create a test directory first
    await async_client.post(
        "/api/v2/rag/create-directory?directory_path=test_stats_directory"
    )

    response = await async_client.get(
        "/api/v2/rag/directories/test_stats_directory/stats"
    )
    assert response.status_code == 200

    data = response.json()
    assert "directory_path" in data
    assert data["directory_path"] == "test_stats_directory"
    assert "document_count" in data
    assert "total_chunks" in data
    assert "total_size_mb" in data
    assert "last_updated" in data
    assert "documents" in data


@pytest.mark.asyncio
async def test_rag_bulk_operations(async_client: AsyncClient):
    """Test RAG bulk operations"""
    # Test bulk delete (should work even with empty list)
    response = await async_client.post("/api/v2/rag/documents/bulk-delete", json=[])
    assert response.status_code == 200

    data = response.json()
    assert "message" in data

    # Test bulk move (should work even with empty list)
    response = await async_client.post(
        "/api/v2/rag/documents/bulk-move",
        json={"document_ids": [], "new_directory_path": "test_directory"},
    )
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
