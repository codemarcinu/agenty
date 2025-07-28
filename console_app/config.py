"""
Konfiguracja aplikacji konsolowej
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Klasa konfiguracji aplikacji"""
    
    def __init__(self):
        # Podstawowe ustawienia
        self.BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
        self.OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
        # Katalogi danych
        self.PARAGONY_DIR = os.getenv('PARAGONY_DIR', '/home/marcin/Dokumenty/PROJEKT/AGENTY/PARAGONY')
        self.WIEDZA_RAG_DIR = os.getenv('WIEDZA_RAG_DIR', '/home/marcin/Dokumenty/PROJEKT/AGENTY/WIEDZA_RAG')
        
        # Ustawienia OCR
        self.OCR_TIMEOUT = int(os.getenv('OCR_TIMEOUT', '30'))
        self.OCR_LANGUAGE = os.getenv('OCR_LANGUAGE', 'pol')
        
        # Ustawienia RAG
        self.RAG_CHUNK_SIZE = int(os.getenv('RAG_CHUNK_SIZE', '1000'))
        self.RAG_OVERLAP = int(os.getenv('RAG_OVERLAP', '200'))
        self.RAG_SIMILARITY_THRESHOLD = float(os.getenv('RAG_SIMILARITY_THRESHOLD', '0.65'))
        
        # Ustawienia HTTP
        self.HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', '30'))
        self.HTTP_RETRIES = int(os.getenv('HTTP_RETRIES', '3'))
        
        # Ustawienia logowania
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
        
        # Ustawienia UI
        self.UI_THEME = os.getenv('UI_THEME', 'default')
        self.UI_LANGUAGE = os.getenv('UI_LANGUAGE', 'pl')
        
        # Walidacja katalogów
        self._validate_directories()
    
    def _validate_directories(self):
        """Walidacja katalogów"""
        paragony_path = Path(self.PARAGONY_DIR)
        wiedza_path = Path(self.WIEDZA_RAG_DIR)
        
        # Tworzenie katalogów jeśli nie istnieją
        paragony_path.mkdir(parents=True, exist_ok=True)
        wiedza_path.mkdir(parents=True, exist_ok=True)
        
        # Aktualizacja ścieżek na absolutne
        self.PARAGONY_DIR = str(paragony_path.absolute())
        self.WIEDZA_RAG_DIR = str(wiedza_path.absolute())
    
    def get_backend_health_url(self) -> str:
        """URL do sprawdzenia stanu backendu"""
        return f"{self.BACKEND_URL}/api/health"
    
    def get_receipt_upload_url(self) -> str:
        """URL do uploadu paragonów"""
        return f"{self.BACKEND_URL}/api/v1/receipts/upload"
    
    def get_receipt_validate_url(self) -> str:
        """URL do walidacji paragonów"""
        return f"{self.BACKEND_URL}/api/v1/receipts/validate"
    
    def get_rag_search_url(self) -> str:
        """URL do wyszukiwania RAG"""
        return f"{self.BACKEND_URL}/api/v2/rag/search"
    
    def get_rag_add_url(self) -> str:
        """URL do dodawania dokumentów RAG"""
        return f"{self.BACKEND_URL}/api/v2/rag/add"
    
    def get_statistics_url(self) -> str:
        """URL do statystyk"""
        return f"{self.BACKEND_URL}/api/v1/analytics/statistics"
    
    def to_dict(self) -> dict:
        """Konwersja konfiguracji do słownika"""
        return {
            'backend_url': self.BACKEND_URL,
            'ollama_url': self.OLLAMA_URL,
            'paragony_dir': self.PARAGONY_DIR,
            'wiedza_rag_dir': self.WIEDZA_RAG_DIR,
            'ocr_timeout': self.OCR_TIMEOUT,
            'ocr_language': self.OCR_LANGUAGE,
            'rag_chunk_size': self.RAG_CHUNK_SIZE,
            'rag_overlap': self.RAG_OVERLAP,
            'rag_similarity_threshold': self.RAG_SIMILARITY_THRESHOLD,
            'http_timeout': self.HTTP_TIMEOUT,
            'http_retries': self.HTTP_RETRIES,
            'log_level': self.LOG_LEVEL,
            'ui_theme': self.UI_THEME,
            'ui_language': self.UI_LANGUAGE,
        }
    
    def __str__(self) -> str:
        """String representation"""
        return f"Config(backend={self.BACKEND_URL}, paragony={self.PARAGONY_DIR}, wiedza={self.WIEDZA_RAG_DIR})" 