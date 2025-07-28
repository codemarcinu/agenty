from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, session: AsyncSession, user_id: int) -> dict | None:
        pass

    @abstractmethod
    async def create(self, session: AsyncSession, user_data: dict) -> dict:
        pass


class FoodItemRepository(ABC):
    @abstractmethod
    async def get_by_id(self, session: AsyncSession, item_id: int) -> dict | None:
        pass

    @abstractmethod
    async def create(self, session: AsyncSession, item_data: dict) -> dict:
        pass

    @abstractmethod
    async def search(self, session: AsyncSession, query: str) -> list[dict]:
        pass
