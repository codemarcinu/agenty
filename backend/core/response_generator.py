from typing import Any


class ResponseGenerator:
    async def generate_response(
        self, agent_response: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """
        Generuje końcową odpowiedź na podstawie odpowiedzi agenta i kontekstu.
        W rzeczywistej implementacji powinien formatować odpowiedź i dodawać personalizację.
        """
        return str(agent_response.get("response", "Brak odpowiedzi od agenta."))
