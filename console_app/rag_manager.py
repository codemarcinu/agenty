"""
Moduł do zarządzania RAG (Retrieval-Augmented Generation)
"""

import asyncio
import structlog
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx
from rich.console import Console

from .config import Config

logger = structlog.get_logger()
console = Console()


class RAGManager:
    """Klasa do zarządzania bazą wiedzy RAG"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=self.config.HTTP_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def add_document(self, file_path: Path) -> Dict[str, Any]:
        """Dodawanie dokumentu do bazy wiedzy"""
        try:
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'Plik nie istnieje: {file_path}',
                    'file': str(file_path)
                }
            
            # Sprawdzenie typu pliku
            if not self._is_supported_document(file_path):
                return {
                    'success': False,
                    'error': f'Nieobsługiwany typ dokumentu: {file_path.suffix}',
                    'file': str(file_path)
                }
            
            # Wczytanie zawartości pliku
            content = await self._read_file_content(file_path)
            if not content:
                return {
                    'success': False,
                    'error': 'Nie można wczytać zawartości pliku',
                    'file': str(file_path)
                }
            
            # Dodanie do bazy wiedzy
            url = self.config.get_rag_add_url()
            data = {
                'content': content,
                'source_id': str(file_path),
                'metadata': {
                    'filename': file_path.name,
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'file_type': file_path.suffix.lower()
                }
            }
            
            response = await self.client.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'file': str(file_path),
                    'processed_chunks': result.get('processed_chunks', 0),
                    'source_id': result.get('source_id', str(file_path))
                }
            else:
                logger.error(f"Błąd dodawania dokumentu: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': response.text,
                    'file': str(file_path)
                }
                
        except Exception as e:
            logger.error(f"Błąd dodawania dokumentu {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': str(file_path)
            }
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Wyszukiwanie w bazie wiedzy"""
        try:
            url = self.config.get_rag_search_url()
            data = {
                'query': query,
                'k': limit,
                'min_similarity': self.config.RAG_SIMILARITY_THRESHOLD
            }
            
            response = await self.client.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('results', [])
            else:
                logger.error(f"Błąd wyszukiwania: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Błąd wyszukiwania: {e}")
            return []
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """Lista dokumentów w bazie wiedzy"""
        try:
            # Użyj endpointu do listowania dokumentów (jeśli istnieje)
            url = f"{self.config.BACKEND_URL}/api/v2/rag/documents"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                return response.json().get('documents', [])
            else:
                # Fallback - sprawdź katalog lokalny
                return await self._list_local_documents()
                
        except Exception as e:
            logger.error(f"Błąd listowania dokumentów: {e}")
            return await self._list_local_documents()
    
    async def _list_local_documents(self) -> List[Dict[str, Any]]:
        """Lista dokumentów z katalogu lokalnego"""
        documents = []
        wiedza_dir = Path(self.config.WIEDZA_RAG_DIR)
        
        if not wiedza_dir.exists():
            return documents
        
        for file_path in wiedza_dir.glob("*"):
            if self._is_supported_document(file_path):
                documents.append({
                    'filename': file_path.name,
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'file_type': file_path.suffix.lower(),
                    'modified': file_path.stat().st_mtime
                })
        
        return documents
    
    def _is_supported_document(self, file_path: Path) -> bool:
        """Sprawdzenie czy dokument jest obsługiwany"""
        supported_extensions = ['.txt', '.md', '.pdf', '.docx', '.html']
        return file_path.suffix.lower() in supported_extensions
    
    async def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Wczytanie zawartości pliku"""
        try:
            if file_path.suffix.lower() == '.pdf':
                return await self._read_pdf_content(file_path)
            else:
                # Dla plików tekstowych
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Błąd wczytywania pliku {file_path}: {e}")
            return None
    
    async def _read_pdf_content(self, file_path: Path) -> Optional[str]:
        """Wczytanie zawartości PDF"""
        try:
            # Użyj biblioteki pdfplumber lub podobnej
            import pdfplumber
            
            content = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        content += text + "\n"
            
            return content.strip()
        except ImportError:
            logger.warning("pdfplumber nie jest zainstalowane, nie można wczytać PDF")
            return None
        except Exception as e:
            logger.error(f"Błąd wczytywania PDF {file_path}: {e}")
            return None
    
    async def add_directory(self, directory_path: Path) -> Dict[str, Any]:
        """Dodawanie wszystkich dokumentów z katalogu"""
        results = []
        
        if not directory_path.exists():
            return {
                'success': False,
                'error': f'Katalog nie istnieje: {directory_path}',
                'results': results
            }
        
        # Znajdź wszystkie obsługiwane dokumenty
        supported_files = []
        for ext in ['.txt', '.md', '.pdf', '.docx', '.html']:
            supported_files.extend(directory_path.glob(f"*{ext}"))
            supported_files.extend(directory_path.glob(f"*{ext.upper()}"))
        
        console.print(f"[blue]📚 Znaleziono {len(supported_files)} dokumentów do dodania[/blue]")
        
        # Dodaj dokumenty
        for i, file_path in enumerate(supported_files, 1):
            console.print(f"[blue]📄 Dodawanie {i}/{len(supported_files)}: {file_path.name}[/blue]")
            result = await self.add_document(file_path)
            results.append(result)
            
            # Krótka przerwa między plikami
            await asyncio.sleep(0.1)
        
        successful = sum(1 for r in results if r.get('success', False))
        
        return {
            'success': True,
            'total_files': len(supported_files),
            'successful': successful,
            'failed': len(supported_files) - successful,
            'results': results
        }
    
    async def clear_knowledge_base(self) -> Dict[str, Any]:
        """Czyszczenie bazy wiedzy"""
        try:
            url = f"{self.config.BACKEND_URL}/api/v2/rag/clear"
            response = await self.client.post(url)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Baza wiedzy została wyczyszczona'
                }
            else:
                logger.error(f"Błąd czyszczenia bazy: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Błąd czyszczenia bazy wiedzy: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close(self):
        """Zamknięcie klienta HTTP"""
        await self.client.aclose()
    
    def __del__(self):
        """Destruktor - zamknięcie klienta"""
        try:
            if hasattr(self, 'client') and not self.client.is_closed:
                import asyncio
                import threading
                if threading.current_thread() is threading.main_thread():
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self.close())
                        else:
                            loop.run_until_complete(self.close())
                    except RuntimeError:
                        asyncio.run(self.close())
        except:
            pass 