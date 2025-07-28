"""
Moduł do przetwarzania paragonów
"""

import asyncio
import mimetypes
import structlog
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx
from rich.console import Console

from .config import Config

logger = structlog.get_logger()
console = Console()


class ReceiptProcessor:
    """Klasa do przetwarzania paragonów"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=self.config.HTTP_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def check_backend_connection(self) -> bool:
        """Sprawdzenie połączenia z backendem"""
        try:
            url = self.config.get_backend_health_url()
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Błąd połączenia z backendem: {e}")
            return False
    
    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Przetwarzanie pojedynczego pliku paragonu"""
        try:
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'Plik nie istnieje: {file_path}',
                    'file': str(file_path)
                }
            
            # Sprawdzenie typu pliku
            if not self._is_supported_file(file_path):
                return {
                    'success': False,
                    'error': f'Nieobsługiwany typ pliku: {file_path.suffix}',
                    'file': str(file_path)
                }
            
            # Walidacja pliku
            validation_result = await self._validate_file(file_path)
            if not validation_result.get('can_process', False):
                return {
                    'success': False,
                    'error': 'Plik nie przeszedł walidacji',
                    'file': str(file_path),
                    'validation': validation_result
                }
            
            # Upload i przetwarzanie
            upload_result = await self._upload_and_process(file_path)
            
            return {
                'success': True,
                'file': str(file_path),
                'text': upload_result.get('text', ''),
                'message': upload_result.get('message', ''),
                'validation': validation_result,
                'processing_info': upload_result.get('processing_info', {})
            }
            
        except Exception as e:
            logger.error(f"Błąd przetwarzania pliku {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': str(file_path)
            }
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Sprawdzenie czy plik jest obsługiwany"""
        supported_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']
        return file_path.suffix.lower() in supported_extensions
    
    async def _validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Walidacja pliku przed przetwarzaniem"""
        try:
            url = self.config.get_receipt_validate_url()
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, self._get_mime_type(file_path))}
                data = {'auto_enhance': 'true'}
                
                response = await self.client.post(url, files=files, data=data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Błąd walidacji: {response.status_code} - {response.text}")
                    return {'can_process': False, 'error': response.text}
                    
        except Exception as e:
            logger.error(f"Błąd walidacji pliku {file_path}: {e}")
            return {'can_process': False, 'error': str(e)}
    
    async def _upload_and_process(self, file_path: Path) -> Dict[str, Any]:
        """Upload i przetwarzanie pliku"""
        try:
            url = self.config.get_receipt_upload_url()
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, self._get_mime_type(file_path))}
                data = {'auto_enhance': 'true'}
                
                response = await self.client.post(url, files=files, data=data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Błąd uploadu: {response.status_code} - {response.text}")
                    return {'error': response.text}
                    
        except Exception as e:
            logger.error(f"Błąd uploadu pliku {file_path}: {e}")
            return {'error': str(e)}
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Pobranie typu MIME dla pliku"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'
    
    async def process_directory(self, directory_path: Path) -> List[Dict[str, Any]]:
        """Przetwarzanie wszystkich plików w katalogu"""
        results = []
        
        if not directory_path.exists():
            logger.error(f"Katalog nie istnieje: {directory_path}")
            return results
        
        # Znajdź wszystkie obsługiwane pliki
        supported_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']:
            supported_files.extend(directory_path.glob(f"*{ext}"))
            supported_files.extend(directory_path.glob(f"*{ext.upper()}"))
        
        console.print(f"[blue]📄 Znaleziono {len(supported_files)} plików do przetworzenia[/blue]")
        
        # Przetwarzaj pliki
        for i, file_path in enumerate(supported_files, 1):
            console.print(f"[blue]📄 Przetwarzanie {i}/{len(supported_files)}: {file_path.name}[/blue]")
            result = await self.process_file(file_path)
            results.append(result)
            
            # Krótka przerwa między plikami
            await asyncio.sleep(0.1)
        
        return results
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Pobranie statystyk przetwarzania"""
        try:
            url = self.config.get_statistics_url()
            response = await self.client.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Błąd pobierania statystyk: {response.status_code}")
                return {'error': 'Nie można pobrać statystyk'}
                
        except Exception as e:
            logger.error(f"Błąd pobierania statystyk: {e}")
            return {'error': str(e)}
    
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