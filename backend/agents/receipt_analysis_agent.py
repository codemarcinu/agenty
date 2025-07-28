import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.anti_hallucination_decorator_optimized import with_receipt_validation
from core.anti_hallucination_system import ValidationLevel
import logging

logger = logging.getLogger(__name__)


class ReceiptAnalysisAgent(BaseAgent):
    """Agent odpowiedzialny za analizę danych paragonu po przetworzeniu OCR."""

    def __init__(
        self,
        name: str = "ReceiptAnalysisAgent",
        error_handler=None,
        fallback_manager=None,
        **kwargs,
    ) -> None:
        super().__init__(
            name=name,
            error_handler=error_handler,
            fallback_manager=fallback_manager,
            **kwargs,
        )

    @with_receipt_validation(
        validation_level=ValidationLevel.STRICT
    )
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """Analizuje paragon i wyciąga strukturalne dane"""
        start_time = time.time()

        try:
            # Extract OCR text from input
            ocr_text = input_data.get("ocr_text", "")
            image_path = input_data.get("image_path", "")

            if not ocr_text:
                return AgentResponse(
                    success=False,
                    error="Brak tekstu OCR do analizy",
                    text="Brak tekstu OCR do analizy",
                )

            # Simple fallback parsing
            receipt_data = self._fallback_parse(ocr_text)

            # Update performance metrics
            processing_time = time.time() - start_time

            # Return successful response
            return AgentResponse(
                success=True,
                text="Paragon został pomyślnie przeanalizowany",
                data=receipt_data,
                metadata={
                    "processing_time": processing_time,
                    "items_count": len(receipt_data.get("items", [])),
                    "total_amount": receipt_data.get("total", 0.0)
                }
            )

        except Exception as e:
            logger.error(f"Error in receipt analysis: {e}")
            processing_time = time.time() - start_time

            return AgentResponse(
                success=False,
                error=str(e),
                text=f"Przepraszam, wystąpił błąd podczas analizy paragonu: {e}",
                metadata={"processing_time": processing_time},
            )

    def _fallback_parse(self, ocr_text: str) -> dict[str, Any]:
        """Prosty parser fallback"""
        fallback_data = {
            "store_name": "Nieznany sklep",
            "address": "",
            "date": self._normalize_date(""),
            "time": "",
            "items": [],
            "discounts": [],
            "total": 0.0,
            "total_amount": 0.0
        }
        
        if not ocr_text:
            return fallback_data
            
        lines = ocr_text.strip().split('\n')
        all_text = ' '.join(lines)
        
        # Wykryj sklep
        store_patterns = {
            r'LIDL.*?(?:POLSKA|SP|Z\.?O\.?O\.?)': 'Lidl',
            r'BIEDRONKA.*?(?:SP|Z\.?O\.?O\.?)': 'Biedronka', 
            r'KAUFLAND.*?(?:POLSKA|SP|Z\.?O\.?O\.?)?': 'Kaufland',
            r'TESCO.*?(?:POLSKA|SP|Z\.?O\.?O\.?)?': 'Tesco',
            r'CARREFOUR.*?(?:POLSKA|SP|Z\.?O\.?O\.?)?': 'Carrefour',
        }
        
        for pattern, store in store_patterns.items():
            if re.search(pattern, all_text.upper(), re.IGNORECASE):
                fallback_data["store_name"] = store
                break
                
        # Wykryj datę
        date_patterns = [
            r'(\d{2})\.(\d{2})\.(\d{4})',  # DD.MM.YYYY
            r'(\d{2})/(\d{2})/(\d{4})',   # DD/MM/YYYY 
            r'(\d{4})-(\d{2})-(\d{2})',    # YYYY-MM-DD
            r'(\d{2})-(\d{2})-(\d{4})',    # DD-MM-YYYY
            r'DATA:\s*(\d{2})\.(\d{2})\.(\d{4})',  # DATA: DD.MM.YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, all_text)
            if match:
                groups = match.groups()
                if len(groups) >= 3:
                    # Handle different date formats
                    if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                        year, month, day = groups[:3]
                        fallback_data["date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:  # DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY formats
                        day, month, year = groups[:3]
                        fallback_data["date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                break
        
        # Wykryj sumę - rozszerzone pattern-y
        total_patterns = [
            r'(?:SUMA|RAZEM|TOTAL).*?(\d+[,\.]\d{2})',
            r'RAZEMPLN\s*(\d+[,\.]\d{2})',
            r'DO ZAPŁATY.*?(\d+[,\.]\d{2})',
            r'SUMA PLN.*?(\d+[,\.]\d{2})',
            r'KWOTA.*?(\d+[,\.]\d{2})',
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, all_text.upper())
            if match:
                try:
                    total_value = float(match.group(1).replace(',', '.'))
                    fallback_data["total"] = total_value
                    fallback_data["total_amount"] = total_value
                    break
                except ValueError:
                    continue
        
        # Ekstrakcja produktów
        product_patterns = [
            r'([A-ZĄĆĘŁŃÓŚŹŻ\s]+)\s+(\d+[.,]\d{2})\s*PLN',
            r'([A-ZĄĆĘŁŃÓŚŹŻ\s]+)\s+(\d+[.,]\d{2})',
        ]
        
        filter_words = {
            'SUMA', 'RAZEM', 'TOTAL', 'PTU', 'PODATEK', 'RABAT', 'ZNIŻKA',
            'KARTA', 'PŁATNOŚĆ', 'GOTÓWKA', 'KARTA PŁATNICZA', 'NIP',
            'DATA', 'GODZINA', 'KASA', 'KASJER', 'NUMER', 'TRANSAKCJI',
            'REGON', 'ADRES', 'TELEFON', 'EMAIL', 'WWW', 'PARAGON',
            'FISKALNY', 'KOPIĘ', 'ZACHOWAJ', 'DZIĘKUJEMY', 'ZAPRASZAMY',
            'DO ZAPŁATY', 'OTRZYMANO', 'RESZTA', 'KWOTA'
        }
        
        for pattern in product_patterns:
            matches = re.finditer(pattern, all_text)
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 2:
                    product_name = groups[0].strip()
                    price_str = groups[1].replace(',', '.')
                    
                    # Sprawdź czy to nie jest słowo do filtrowania
                    if any(filter_word in product_name.upper() for filter_word in filter_words):
                        continue
                        
                    # Sprawdź czy nazwa produktu ma sens (min 3 znaki)
                    if len(product_name) < 3:
                        continue
                        
                    try:
                        price = float(price_str)
                        
                        # Sprawdź czy cena jest rozsądna (0.01 - 1000 PLN)
                        if 0.01 <= price <= 1000:
                            fallback_data["items"].append({
                                "name": product_name,
                                "quantity": 1.0,
                                "unit_price": price,
                                "total_price": price,
                                "tax_category": "A"
                            })
                            
                    except ValueError:
                        continue
                        
        # Jeśli nie ma sumy, oblicz z produktów
        if fallback_data["total"] == 0.0 and fallback_data["items"]:
            calculated_total = sum(item.get("total_price", 0) for item in fallback_data["items"])
            fallback_data["total"] = round(calculated_total, 2)
            fallback_data["total_amount"] = round(calculated_total, 2)
            
        return fallback_data

    def _normalize_date(self, date_str: str) -> str:
        """Normalizuje datę"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Sprawdź czy data jest już w formacie YYYY-MM-DD
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return date_str
            
            # Próbuj różne formaty dat
            date_formats = [
                '%d.%m.%Y',  # DD.MM.YYYY
                '%Y-%m-%d',  # YYYY-MM-DD
                '%d/%m/%Y',  # DD/MM/YYYY
            ]
            
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
                    
            # Jeśli nie udało się sparsować, zwróć dzisiejszą datę
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.warning(f"Date normalization error: {e}")
            return datetime.now().strftime('%Y-%m-%d')


class EnhancedReceiptAnalysisAgent(ReceiptAnalysisAgent):
    """Rozszerzona wersja agenta do analizy paragonów"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(name="EnhancedReceiptAnalysisAgent", **kwargs)

    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """Przetwarza tekst OCR i wyciąga strukturalne dane paragonu"""
        return await super().process(input_data)
