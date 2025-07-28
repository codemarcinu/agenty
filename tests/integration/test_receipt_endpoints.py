
import pytest


@pytest.mark.asyncio
async def test_upload_receipt_success(async_client, mock_receipt_processor):
    """Test udanego uploadu paragonu."""
    mock_receipt_processor.return_value = {
        "success": True,
        "message": "Receipt processed successfully",
        "data": {
            "items": [
                {"name": "Milk", "price": 2.50, "quantity": 1},
                {"name": "Bread", "price": 1.20, "quantity": 2},
            ],
            "total": 3.90,
            "date": "2024-01-15",
        },
    }

    files = {"file": ("receipt.jpg", b"fake_image_data", "image/jpeg")}
    response = await async_client.post("/api/v2/receipts/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    assert "data" in data


@pytest.mark.asyncio
async def test_upload_receipt_invalid_file(async_client):
    """Test uploadu nieprawidłowego pliku."""
    files = {"file": ("test.txt", b"not an image", "text/plain")}
    response = await async_client.post("/api/v2/receipts/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_upload_receipt_processing_error(async_client, mock_receipt_processor):
    """Test błędu przetwarzania paragonu."""
    mock_receipt_processor.side_effect = Exception("Processing failed")

    files = {"file": ("receipt.jpg", b"fake_image_data", "image/jpeg")}
    response = await async_client.post("/api/v2/receipts/upload", files=files)

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_analyze_receipt_text_success(async_client, mock_receipt_analyzer):
    """Test udanej analizy tekstu paragonu."""
    mock_receipt_analyzer.return_value = {
        "success": True,
        "message": "Receipt analyzed successfully",
        "data": {
            "items": [
                {"name": "Milk", "price": 2.50, "quantity": 1},
                {"name": "Bread", "price": 1.20, "quantity": 2},
            ],
            "total": 3.90,
            "date": "2024-01-15",
        },
    }

    receipt_data = {"text": "Milk 2.50\nBread 1.20 x2\nTotal: 3.90"}
    response = await async_client.post("/api/v2/receipts/analyze", json=receipt_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    assert "data" in data


@pytest.mark.asyncio
async def test_analyze_receipt_text_error(async_client, mock_receipt_analyzer):
    """Test błędu analizy tekstu paragonu."""
    mock_receipt_analyzer.side_effect = Exception("Analysis failed")

    receipt_data = {"text": "Invalid receipt text"}
    response = await async_client.post("/api/v2/receipts/analyze", json=receipt_data)

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_receipt_history_success(async_client, mock_db_session):
    """Test pobierania historii paragonów."""
    mock_receipts = [
        {"id": 1, "filename": "receipt1.jpg", "upload_date": "2024-01-15"},
        {"id": 2, "filename": "receipt2.jpg", "upload_date": "2024-01-16"},
    ]
    mock_db_session.return_value.__enter__.return_value.query.return_value.all.return_value = (
        mock_receipts
    )

    response = await async_client.get("/api/v2/receipts/history")

    assert response.status_code == 200
    data = response.json()
    assert "receipts" in data
    assert len(data["receipts"]) == 2


@pytest.mark.asyncio
async def test_get_receipt_history_empty(async_client, mock_db_session):
    """Test pobierania pustej historii paragonów."""
    mock_db_session.return_value.__enter__.return_value.query.return_value.all.return_value = (
        []
    )

    response = await async_client.get("/api/v2/receipts/history")

    assert response.status_code == 200
    data = response.json()
    assert "receipts" in data
    assert len(data["receipts"]) == 0


@pytest.mark.asyncio
async def test_delete_receipt_success(async_client, mock_db_session):
    """Test udanego usuwania paragonu."""
    mock_receipt = {"id": 1, "filename": "receipt1.jpg"}
    mock_db_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = (
        mock_receipt
    )

    response = await async_client.delete("/api/v2/receipts/1")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_delete_receipt_not_found(async_client, mock_db_session):
    """Test usuwania nieistniejącego paragonu."""
    mock_db_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = (
        None
    )

    response = await async_client.delete("/api/v2/receipts/999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
