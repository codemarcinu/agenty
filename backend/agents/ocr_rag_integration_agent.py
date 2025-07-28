"""
OCR-RAG Integration Agent

This agent integrates OCR processing with the RAG system by automatically
adding OCR-extracted text to the knowledge base for future retrieval.
"""

from datetime import datetime
import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from agents.ocr_agent import OCRAgent, OCRAgentInput
from core.rag_document_processor import RAGDocumentProcessor
from core.rag_integration import RAGDatabaseIntegration

logger = logging.getLogger(__name__)


class OCRRAGIntegrationAgent(BaseAgent):
    """
    Agent that integrates OCR processing with RAG system.

    This agent:
    1. Processes images/PDFs with OCR
    2. Extracts structured data from receipts
    3. Adds extracted content to RAG knowledge base
    4. Enables future queries about shopping history
    """

    def __init__(self, name: str = "OCRRAGIntegrationAgent", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

        # Initialize OCR agent
        self.ocr_agent = OCRAgent()

        # Initialize RAG components
        self.rag_processor = RAGDocumentProcessor()
        self.rag_integration = RAGDatabaseIntegration(self.rag_processor)

        # Metadata for RAG documents
        self.document_metadata = {
            "source_type": "receipt_ocr",
            "processing_agent": self.name,
            "created_at": datetime.now().isoformat(),
        }

    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Process file with OCR and add to RAG knowledge base

        Args:
            input_data: Dictionary containing:
                - file_bytes: File content as bytes
                - file_type: Type of file ('image' or 'pdf')
                - filename: Original filename
                - session_id: User session ID
                - store_info: Optional store information
                - receipt_date: Optional receipt date

        Returns:
            AgentResponse with OCR results and RAG integration status
        """
        try:
            # Extract input data
            file_bytes = input_data.get("file_bytes")
            file_type = input_data.get("file_type", "image")
            filename = input_data.get("filename", "unknown")
            session_id = input_data.get("session_id", "unknown")
            store_info = input_data.get("store_info", {})
            receipt_date = input_data.get("receipt_date")

            if not file_bytes:
                return AgentResponse(
                    success=False,
                    error="No file content provided",
                    text="Brak zawartości pliku do przetworzenia",
                )

            logger.info(f"Starting OCR-RAG integration for {filename}")

            # Step 1: OCR Processing
            ocr_input = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)

            ocr_result = await self.ocr_agent.process(ocr_input)

            if not ocr_result.success:
                return AgentResponse(
                    success=False,
                    error=f"OCR processing failed: {ocr_result.error}",
                    text="Błąd podczas przetwarzania OCR",
                )

            extracted_text = ocr_result.text or ""
            ocr_confidence = getattr(ocr_result, "confidence", 0.5)

            logger.info(f"OCR completed for {filename}, confidence: {ocr_confidence}")

            # Step 2: Create RAG document content
            rag_content = self._create_rag_content(
                extracted_text=extracted_text,
                filename=filename,
                store_info=store_info,
                receipt_date=receipt_date,
                ocr_confidence=ocr_confidence,
            )

            # Step 3: Create metadata for RAG
            rag_metadata = self._create_rag_metadata(
                filename=filename,
                session_id=session_id,
                store_info=store_info,
                receipt_date=receipt_date,
                ocr_confidence=ocr_confidence,
                file_type=file_type,
            )

            # Step 4: Add to RAG knowledge base
            source_id = (
                f"receipt_ocr_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            chunks = await self.rag_processor.process_document(
                content=rag_content, source_id=source_id, metadata=rag_metadata
            )

            logger.info(f"Added {len(chunks)} chunks to RAG for {filename}")

            # Step 5: Return comprehensive response
            return AgentResponse(
                success=True,
                text=f"Pomyślnie przetworzono paragon {filename} i dodano do bazy wiedzy",
                data={
                    "ocr_text": extracted_text,
                    "ocr_confidence": ocr_confidence,
                    "rag_chunks_added": len(chunks),
                    "rag_source_id": source_id,
                    "filename": filename,
                    "store_info": store_info,
                    "receipt_date": receipt_date,
                    "file_type": file_type,
                },
                metadata={
                    "processing_time": getattr(ocr_result, "metadata", {}).get(
                        "processing_time", 0
                    ),
                    "rag_integration": True,
                    "chunks_processed": len(chunks),
                },
            )

        except Exception as e:
            logger.error(f"Error in OCR-RAG integration: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas integracji OCR-RAG: {e!s}",
                text="Wystąpił błąd podczas przetwarzania",
            )

    def _create_rag_content(
        self,
        extracted_text: str,
        filename: str,
        store_info: dict[str, Any],
        receipt_date: str | None,
        ocr_confidence: float,
    ) -> str:
        """Create structured content for RAG from OCR text"""

        # Format store information
        store_name = store_info.get("name", "Nieznany sklep")
        store_address = store_info.get("address", "")

        # Format receipt date
        date_info = (
            f"Data paragonu: {receipt_date}" if receipt_date else "Data nieznana"
        )

        # Create structured content
        content = f"""
PARAGON - {filename}

{date_info}
Sklep: {store_name}
{f"Adres: {store_address}" if store_address else ""}
Pewność OCR: {ocr_confidence:.2f}

ZAWARTOŚĆ PARAGONU:
{extracted_text}

---
Ten dokument został automatycznie przetworzony przez system OCR i dodany do bazy wiedzy.
Można go wyszukiwać w kontekście historii zakupów i analizy wydatków.
"""

        return content

    def _create_rag_metadata(
        self,
        filename: str,
        session_id: str,
        store_info: dict[str, Any],
        receipt_date: str | None,
        ocr_confidence: float,
        file_type: str,
    ) -> dict[str, Any]:
        """Create metadata for RAG document"""

        metadata = self.document_metadata.copy()
        metadata.update(
            {
                "filename": filename,
                "session_id": session_id,
                "store_name": store_info.get("name", "Nieznany sklep"),
                "store_address": store_info.get("address", ""),
                "receipt_date": receipt_date,
                "ocr_confidence": ocr_confidence,
                "file_type": file_type,
                "tags": ["receipt", "ocr", "shopping", "expenses"],
                "category": "receipts",
                "processing_timestamp": datetime.now().isoformat(),
            }
        )

        return metadata

    async def query_receipt_history(
        self, query: str, session_id: str | None = None, limit: int = 5
    ) -> AgentResponse:
        """
        Query receipt history using RAG

        Args:
            query: Search query
            session_id: Optional session ID to filter results
            limit: Maximum number of results

        Returns:
            AgentResponse with search results
        """
        try:
            # Add session filter to query if provided
            enhanced_query = f"{query} (session: {session_id})" if session_id else query

            # For now, return a simple response indicating the feature is available
            # In a full implementation, this would use the vector store search
            return AgentResponse(
                success=True,
                text=f"Funkcja wyszukiwania historii paragonów jest dostępna. Zapytanie: {enhanced_query}",
                data={
                    "results": [],
                    "query": query,
                    "total_results": 0,
                    "note": "RAG search integration in development",
                },
            )

        except Exception as e:
            logger.error(f"Error querying receipt history: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas wyszukiwania historii paragonów: {e!s}",
                text="Wystąpił błąd podczas wyszukiwania",
            )

    async def get_receipt_statistics(
        self,
        session_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> AgentResponse:
        """
        Get statistics about processed receipts

        Args:
            session_id: Optional session ID to filter
            date_from: Optional start date
            date_to: Optional end date

        Returns:
            AgentResponse with statistics
        """
        try:
            # For now, return basic statistics
            # In a full implementation, this would query the vector store
            return AgentResponse(
                success=True,
                text="Statystyki paragonów są dostępne",
                data={
                    "total_receipts": 0,
                    "total_stores": 0,
                    "average_ocr_confidence": 0.0,
                    "date_range": {"from": date_from, "to": date_to},
                    "session_id": session_id,
                    "note": "Statistics integration in development",
                },
            )

        except Exception as e:
            logger.error(f"Error getting receipt statistics: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas pobierania statystyk: {e!s}",
                text="Wystąpił błąd podczas analizy statystyk",
            )
