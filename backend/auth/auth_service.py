"""
Authentication service for user management
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from auth.jwt_handler import jwt_handler
from auth.models import User
from auth.schemas import UserCreate, UserLogin, UserResponse

logger = structlog.get_logger()


class AuthService:
    """Service class for authentication operations"""

    def __init__(self, db_session: AsyncSession):
        """Initialize AuthService with database session"""
        self.db_session = db_session

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        try:
            # Check if user already exists by username
            stmt = select(User).where(User.username == user_data.username)
            result = await self.db_session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise ValueError("Username already registered")

            # Check if user already exists by email
            stmt = select(User).where(User.email == user_data.email)
            result = await self.db_session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise ValueError("Email already registered")

            # Create new user
            hashed_password = jwt_handler.get_password_hash(user_data.password)
            user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
            )

            self.db_session.add(user)
            await self.db_session.commit()
            await self.db_session.refresh(user)

            logger.info(f"New user registered: {user.email}")

            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                roles=[],
            )

        except ValueError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error registering user: {e}")
            raise ValueError("Error creating user")

    async def authenticate_user(self, user_data: UserLogin) -> UserResponse | None:
        """Authenticate user and return user info if successful"""
        try:
            # Find user by email with eager loading of roles
            stmt = (
                select(User)
                .options(selectinload(User.roles))
                .where(User.email == user_data.email)
            )
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            if not jwt_handler.verify_password(
                user_data.password, user.hashed_password
            ):
                return None

            if not user.is_active:
                return None

            # Update last login
            user.last_login = datetime.utcnow()
            await self.db_session.commit()

            # Get user roles (already loaded)
            roles = [role.name for role in user.roles] if user.roles else []

            logger.info(f"User authenticated: {user.email}")

            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                roles=roles,
            )

        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None

    async def get_user_by_username(self, username: str) -> UserResponse | None:
        """Get user by username"""
        try:
            stmt = (
                select(User)
                .options(selectinload(User.roles))
                .where(User.username == username)
            )
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            roles = [role.name for role in user.roles] if user.roles else []

            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                roles=roles,
            )

        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

    async def get_user_by_email(self, email: str) -> UserResponse | None:
        """Get user by email"""
        try:
            stmt = (
                select(User)
                .options(selectinload(User.roles))
                .where(User.email == email)
            )
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            roles = [role.name for role in user.roles] if user.roles else []

            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                roles=roles,
            )

        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    async def update_user(self, user_id: int, **kwargs) -> UserResponse | None:
        """Update user information"""
        try:
            stmt = (
                select(User).options(selectinload(User.roles)).where(User.id == user_id)
            )
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Update fields
            for field, value in kwargs.items():
                if hasattr(user, field):
                    setattr(user, field, value)

            user.updated_at = datetime.utcnow()
            await self.db_session.commit()
            await self.db_session.refresh(user)

            roles = [role.name for role in user.roles] if user.roles else []

            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                roles=roles,
            )

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating user: {e}")
            return None

    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return False

            await self.db_session.delete(user)
            await self.db_session.commit()

            logger.info(f"User deleted: {user.email}")
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error deleting user: {e}")
            return False

    async def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return False

            if not jwt_handler.verify_password(old_password, user.hashed_password):
                return False

            user.hashed_password = jwt_handler.get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            await self.db_session.commit()

            logger.info(f"Password changed for user: {user.email}")
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error changing password: {e}")
            return False

    async def activate_user(self, user_id: int) -> bool:
        """Activate user account"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return False

            user.is_active = True
            user.updated_at = datetime.utcnow()
            await self.db_session.commit()

            logger.info(f"User activated: {user.email}")
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error activating user: {e}")
            return False

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return False

            user.is_active = False
            user.updated_at = datetime.utcnow()
            await self.db_session.commit()

            logger.info(f"User deactivated: {user.email}")
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error deactivating user: {e}")
            return False
