"""
Moduł do eksportu wyników przetwarzania
"""

import json
import csv
import structlog
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from rich.console import Console

logger = structlog.get_logger()
console = Console()


class ExportManager:
    """Klasa do eksportu wyników przetwarzania"""
    
    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_receipt_results(self, results: List[Dict[str, Any]], format: str = "json") -> Dict[str, Any]:
        """Eksport wyników przetwarzania paragonów"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == "json":
                return await self._export_to_json(results, timestamp, "receipts")
            elif format.lower() == "csv":
                return await self._export_to_csv(results, timestamp, "receipts")
            elif format.lower() == "txt":
                return await self._export_to_txt(results, timestamp, "receipts")
            else:
                return {
                    'success': False,
                    'error': f'Nieobsługiwany format: {format}'
                }
                
        except Exception as e:
            logger.error(f"Błąd eksportu wyników: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def export_rag_results(self, results: List[Dict[str, Any]], format: str = "json") -> Dict[str, Any]:
        """Eksport wyników wyszukiwania RAG"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == "json":
                return await self._export_to_json(results, timestamp, "rag_search")
            elif format.lower() == "csv":
                return await self._export_to_csv(results, timestamp, "rag_search")
            elif format.lower() == "txt":
                return await self._export_to_txt(results, timestamp, "rag_search")
            else:
                return {
                    'success': False,
                    'error': f'Nieobsługiwany format: {format}'
                }
                
        except Exception as e:
            logger.error(f"Błąd eksportu wyników RAG: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _export_to_json(self, results: List[Dict[str, Any]], timestamp: str, prefix: str) -> Dict[str, Any]:
        """Eksport do formatu JSON"""
        try:
            filename = f"{prefix}_{timestamp}.json"
            filepath = self.export_dir / filename
            
            export_data = {
                'export_info': {
                    'timestamp': timestamp,
                    'export_date': datetime.now().isoformat(),
                    'total_results': len(results),
                    'format': 'json'
                },
                'results': results
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'format': 'json',
                'total_results': len(results)
            }
            
        except Exception as e:
            logger.error(f"Błąd eksportu do JSON: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _export_to_csv(self, results: List[Dict[str, Any]], timestamp: str, prefix: str) -> Dict[str, Any]:
        """Eksport do formatu CSV"""
        try:
            filename = f"{prefix}_{timestamp}.csv"
            filepath = self.export_dir / filename
            
            if not results:
                return {
                    'success': False,
                    'error': 'Brak wyników do eksportu'
                }
            
            # Określ kolumny na podstawie pierwszego wyniku
            fieldnames = self._get_csv_fieldnames(results[0])
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    # Spłaszcz zagnieżdżone struktury
                    flat_result = self._flatten_dict(result)
                    writer.writerow(flat_result)
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'format': 'csv',
                'total_results': len(results),
                'columns': fieldnames
            }
            
        except Exception as e:
            logger.error(f"Błąd eksportu do CSV: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _export_to_txt(self, results: List[Dict[str, Any]], timestamp: str, prefix: str) -> Dict[str, Any]:
        """Eksport do formatu TXT"""
        try:
            filename = f"{prefix}_{timestamp}.txt"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Eksport wyników - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*50 + "\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"Wynik {i}:\n")
                    f.write("-"*30 + "\n")
                    
                    if prefix == "receipts":
                        self._write_receipt_to_txt(f, result)
                    elif prefix == "rag_search":
                        self._write_rag_result_to_txt(f, result)
                    
                    f.write("\n")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'format': 'txt',
                'total_results': len(results)
            }
            
        except Exception as e:
            logger.error(f"Błąd eksportu do TXT: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_csv_fieldnames(self, sample_result: Dict[str, Any]) -> List[str]:
        """Określenie kolumn CSV na podstawie przykładowego wyniku"""
        fieldnames = set()
        
        def extract_fields(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    field_name = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        extract_fields(value, field_name)
                    else:
                        fieldnames.add(field_name)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_fields(item, f"{prefix}[{i}]")
        
        extract_fields(sample_result)
        return sorted(list(fieldnames))
    
    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Spłaszczenie zagnieżdżonego słownika"""
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Konwertuj listy na string
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _write_receipt_to_txt(self, file, result: Dict[str, Any]):
        """Zapisanie wyniku paragonu do pliku TXT"""
        file.write(f"Plik: {result.get('file', 'Nieznany')}\n")
        file.write(f"Status: {'✅ Pomyślnie' if result.get('success') else '❌ Błąd'}\n")
        
        if result.get('success'):
            text = result.get('text', '')
            if text:
                file.write(f"Tekst OCR:\n{text}\n")
            
            processing_info = result.get('processing_info', {})
            if processing_info:
                file.write(f"Rozmiar: {processing_info.get('file_size', 0)} bajtów\n")
                file.write(f"Format: {processing_info.get('format', 'Nieznany')}\n")
        else:
            file.write(f"Błąd: {result.get('error', 'Nieznany błąd')}\n")
    
    def _write_rag_result_to_txt(self, file, result: Dict[str, Any]):
        """Zapisanie wyniku RAG do pliku TXT"""
        file.write(f"Źródło: {result.get('source', 'Nieznane')}\n")
        file.write(f"Podobieństwo: {result.get('similarity', 0):.2f}\n")
        
        content = result.get('content', '')
        if content:
            file.write(f"Treść:\n{content}\n")
    
    async def list_exports(self) -> List[Dict[str, Any]]:
        """Lista dostępnych eksportów"""
        exports = []
        
        for file_path in self.export_dir.glob("*"):
            if file_path.is_file():
                exports.append({
                    'filename': file_path.name,
                    'filepath': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime,
                    'format': file_path.suffix.lower()
                })
        
        return sorted(exports, key=lambda x: x['modified'], reverse=True)
    
    async def delete_export(self, filename: str) -> Dict[str, Any]:
        """Usunięcie eksportu"""
        try:
            file_path = self.export_dir / filename
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'Plik nie istnieje: {filename}'
                }
            
            file_path.unlink()
            
            return {
                'success': True,
                'message': f'Usunięto plik: {filename}'
            }
            
        except Exception as e:
            logger.error(f"Błąd usuwania eksportu: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_export_content(self, filename: str) -> Dict[str, Any]:
        """Pobranie zawartości eksportu"""
        try:
            file_path = self.export_dir / filename
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'Plik nie istnieje: {filename}'
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'success': True,
                'filename': filename,
                'content': content,
                'size': len(content)
            }
            
        except Exception as e:
            logger.error(f"Błąd odczytu eksportu: {e}")
            return {
                'success': False,
                'error': str(e)
            } 