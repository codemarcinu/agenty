"""
E2E Auth Fixes Tests
Tests for authentication flow with proper database mocking
Following .cursorrules standards for Python testing
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from pydantic import ValidationError
import pytest

from backend.auth.auth_service import AuthService
from backend.auth.schemas import UserCreate, UserLogin
from backend.core.security import create_access_token, verify_password


class TestE2EAuthFixes:
    """Test cases for E2E authentication flow."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing."""
        mock_session = AsyncMock()

        # Configure mock to handle common database operations
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        return mock_session

    @pytest.fixture
    def auth_service(self, mock_db_session):
        """Create AuthService instance with mocked database."""
        return AuthService(db_session=mock_db_session)

    @pytest.fixture
    def test_user_data(self):
        """Test user data for authentication tests."""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        }

    @pytest.fixture
    def mock_user(self, test_user_data):
        """Create mock user object."""
        user = MagicMock()
        user.id = 1
        user.username = test_user_data["username"]
        user.email = test_user_data["email"]
        user.full_name = test_user_data["full_name"]
        user.is_active = True
        user.is_verified = False
        user.created_at = datetime.now()
        user.updated_at = datetime.now()
        user.last_login = None
        user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5u.Gi"  # testpassword123
        user.roles = []  # Lista zamiast MagicMock
        return user

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, auth_service, test_user_data, mock_db_session
    ):
        """Test successful user registration."""
        # Każde execute() zwraca osobny mock z odpowiednim scalar_one_or_none
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = None
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None
        mock_db_session.execute.side_effect = [mock_result1, mock_result2]
        mock_db_session.commit = AsyncMock()

        # Create user data
        user_create = UserCreate(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"],
        )

        # Mock user creation
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = user_create.username
        mock_user.email = user_create.email
        mock_user.full_name = user_create.full_name
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.roles = []

        # Mock add and refresh
        mock_db_session.add = MagicMock()

        async def refresh_side_effect(user):
            user.id = mock_user.id
            user.username = mock_user.username
            user.email = mock_user.email
            user.full_name = mock_user.full_name
            user.is_active = mock_user.is_active
            user.is_verified = mock_user.is_verified
            user.created_at = mock_user.created_at
            user.updated_at = mock_user.updated_at
            user.last_login = mock_user.last_login
            user.roles = mock_user.roles

        mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        # Test registration
        result = await auth_service.register_user(user_create)

        # Verify result
        assert result is not None
        assert result.username == test_user_data["username"]
        assert result.email == test_user_data["email"]
        assert result.full_name == test_user_data["full_name"]
        assert result.is_active is True

        # Verify database operations were called
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(
        self, auth_service, test_user_data, mock_db_session, mock_user
    ):
        """Test user registration with duplicate username."""
        # Mock existing user
        mock_db_session.execute.return_value.scalars.return_value.first.return_value = (
            mock_user
        )

        # Create user data
        user_create = UserCreate(
            username=test_user_data["username"],
            email="different@example.com",
            password=test_user_data["password"],
            full_name="Different User",
        )

        # Test registration should fail
        with pytest.raises(ValueError, match="Username already registered"):
            await auth_service.register_user(user_create)

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(
        self, auth_service, test_user_data, mock_db_session, mock_user
    ):
        """Test user registration with duplicate email."""
        # Pierwszy execute (username) -> None, drugi (email) -> mock_user
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = None
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.side_effect = [mock_result1, mock_result2]

        # Create user data with different username but same email
        user_create = UserCreate(
            username="differentuser",
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name="Different User",
        )

        # Test registration should fail
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register_user(user_create)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, test_user_data, mock_db_session):
        """Test successful user login."""
        # Tworzę mock_user bezpośrednio w teście
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []


        # Mock user lookup - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        # Create login data
        user_login = UserLogin(
            email=test_user_data["email"], password=test_user_data["password"]
        )


        # Test login
        result = await auth_service.authenticate_user(user_login)


        # Verify result
        assert result is not None
        assert result.username == test_user_data["username"]
        assert result.email == test_user_data["email"]
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self, auth_service, test_user_data, mock_db_session
    ):
        """Test login with invalid credentials."""
        # Mock user not found - execute zwraca None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Create login data
        user_login = UserLogin(email=test_user_data["email"], password="wrongpassword")

        # Test login should fail
        result = await auth_service.authenticate_user(user_login)
        assert result is None

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, auth_service, test_user_data, mock_db_session
    ):
        """Test login with inactive user."""
        # Tworzę mock_user z is_active=False
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = False  # Nieaktywny użytkownik
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []

        # Mock inactive user - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        # Create login data
        user_login = UserLogin(
            email=test_user_data["email"], password=test_user_data["password"]
        )

        # Test login should fail
        result = await auth_service.authenticate_user(user_login)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_access_token(self, test_user_data):
        """Test access token creation."""
        # Create token data
        data = {"sub": test_user_data["username"], "email": test_user_data["email"]}

        # Create token
        token = create_access_token(data=data)

        # Verify token
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_verify_password(self, auth_service, test_user_data):
        """Test password verification."""
        # Test with correct password
        plain_password = "testpassword123"
        hashed_password = "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"

        result = verify_password(plain_password, hashed_password)
        assert result is True

        # Test with incorrect password
        wrong_password = "wrongpassword"
        result = verify_password(wrong_password, hashed_password)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_by_username(
        self, auth_service, test_user_data, mock_db_session
    ):
        """Test get user by username."""
        # Tworzę mock_user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []

        # Mock user lookup - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        # Test get user by username
        result = await auth_service.get_user_by_username(test_user_data["username"])

        # Verify result
        assert result is not None
        assert result.username == test_user_data["username"]
        assert result.email == test_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_user_by_email(
        self, auth_service, test_user_data, mock_db_session
    ):
        """Test get user by email."""
        # Tworzę mock_user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []

        # Mock user lookup - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        # Test get user by email
        result = await auth_service.get_user_by_email(test_user_data["email"])

        # Verify result
        assert result is not None
        assert result.username == test_user_data["username"]
        assert result.email == test_user_data["email"]

    @pytest.mark.asyncio
    async def test_update_user(self, auth_service, test_user_data, mock_db_session):
        """Test update user."""
        # Tworzę mock_user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []

        # Mock user lookup - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        # Update data
        update_data = {"full_name": "Updated User", "email": "updated@example.com"}

        # Test update
        result = await auth_service.update_user(1, **update_data)

        # Verify result
        assert result is not None
        assert result.full_name == "Updated User"
        assert result.email == "updated@example.com"

        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user(self, auth_service, test_user_data, mock_db_session):
        """Test delete user."""
        # Tworzę mock_user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []

        # Mock user lookup - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        # Test deletion
        result = await auth_service.delete_user(1)

        # Verify result
        assert result is True

        # Verify database operations
        mock_db_session.delete.assert_called_once_with(mock_user)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password(self, auth_service, test_user_data, mock_db_session):
        """Test change password."""
        # Tworzę mock_user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []

        # Mock user lookup - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        # Test password change
        new_password = "newpassword123"
        result = await auth_service.change_password(
            1, test_user_data["password"], new_password
        )

        # Verify result
        assert result is True

    @pytest.mark.asyncio
    async def test_change_password_invalid_old_password(
        self, auth_service, test_user_data, mock_db_session, mock_user
    ):
        """Test password change with invalid old password."""
        # Mock user lookup
        mock_db_session.execute.return_value.scalars.return_value.first.return_value = (
            mock_user
        )

        # Test password change with wrong old password
        new_password = "newpassword123"
        result = await auth_service.change_password(
            test_user_data["username"], "wrongoldpassword", new_password
        )

        # Verify result
        assert result is False

    @pytest.mark.asyncio
    async def test_activate_user(self, auth_service, test_user_data, mock_db_session):
        """Test activate user."""
        # Tworzę mock_user z is_active=False
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = False  # Nieaktywny użytkownik
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []

        # Mock user lookup - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        # Test activation
        result = await auth_service.activate_user(1)

        # Verify result
        assert result is True
        assert mock_user.is_active is True

    @pytest.mark.asyncio
    async def test_deactivate_user(self, auth_service, test_user_data, mock_db_session):
        """Test deactivate user."""
        # Tworzę mock_user z is_active=True
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True  # Aktywny użytkownik
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = (
            "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"
        )
        mock_user.roles = []

        # Mock user lookup - execute zwraca mock_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        # Test deactivation
        result = await auth_service.deactivate_user(1)

        # Verify result
        assert result is True
        assert mock_user.is_active is False


class TestAuthFlowIntegration:
    """Test cases for complete authentication flow."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing."""
        mock_session = AsyncMock()
        # Configure mock to handle common database operations
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        return mock_session

    @pytest.fixture
    def auth_flow_service(self, mock_db_session):
        from backend.auth.auth_service import AuthService

        return AuthService(db_session=mock_db_session)

    @pytest.fixture
    def test_user_data(self):
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        }

    @pytest.mark.asyncio
    async def test_complete_auth_flow(
        self, auth_flow_service, test_user_data, mock_db_session
    ):
        # Reset mock for each test with proper side_effect
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        mock_db_session.execute.side_effect = None
        mock_db_session.commit = AsyncMock()

        # Mock refresh to set user attributes
        async def refresh_side_effect(user):
            user.id = 1
            user.is_active = True
            user.is_verified = False
            user.created_at = datetime.now()
            user.updated_at = datetime.now()
            user.last_login = None

        mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)
        mock_db_session.add = MagicMock()

        user_create = UserCreate(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"],
        )

        registered_user = await auth_flow_service.register_user(user_create)
        assert registered_user is not None
        assert registered_user.username == test_user_data["username"]

        # Step 2: Login user - create proper mock User object
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"  # testpassword123
        mock_user.roles = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        user_login = UserLogin(
            email=test_user_data["email"], password=test_user_data["password"]
        )

        logged_in_user = await auth_flow_service.authenticate_user(user_login)
        assert logged_in_user is not None
        assert logged_in_user.username == test_user_data["username"]

        # Step 3: Update user
        mock_user.full_name = "Updated Name"  # Update the mock user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        updated_user = await auth_flow_service.update_user(1, full_name="Updated Name")
        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"

        # Step 4: Delete user
        mock_db_session.delete = AsyncMock()
        deletion_result = await auth_flow_service.delete_user(1)  # Use user ID
        assert deletion_result is True

    @pytest.mark.asyncio
    async def test_auth_flow_with_password_change(
        self, auth_flow_service, test_user_data, mock_db_session
    ):
        # Reset mock for each test with proper side_effect
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        mock_db_session.execute.side_effect = None
        mock_db_session.commit = AsyncMock()

        # Mock refresh to set user attributes
        async def refresh_side_effect(user):
            user.id = 1
            user.is_active = True
            user.is_verified = False
            user.created_at = datetime.now()
            user.updated_at = datetime.now()
            user.last_login = None

        mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)
        mock_db_session.add = MagicMock()

        user_create = UserCreate(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"],
        )

        registered_user = await auth_flow_service.register_user(user_create)
        assert registered_user is not None

        # Login with original password - create proper mock User object
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"  # testpassword123
        mock_user.roles = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        user_login = UserLogin(
            email=test_user_data["email"], password=test_user_data["password"]
        )

        logged_in_user = await auth_flow_service.authenticate_user(user_login)
        assert logged_in_user is not None

        # Change password
        new_password = "newpassword123"
        password_change_result = await auth_flow_service.change_password(
            1, test_user_data["password"], new_password  # Use user ID
        )
        assert password_change_result is True

        # Login with new password
        new_user_login = UserLogin(email=test_user_data["email"], password=new_password)

        new_logged_in_user = await auth_flow_service.authenticate_user(new_user_login)
        assert new_logged_in_user is not None

    @pytest.mark.asyncio
    async def test_auth_flow_with_activation(
        self, auth_flow_service, test_user_data, mock_db_session
    ):
        """Test auth flow with user activation/deactivation."""
        # Register user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        mock_db_session.execute.side_effect = None
        mock_db_session.commit = AsyncMock()

        # Mock refresh to set user attributes
        async def refresh_side_effect(user):
            user.id = 1
            user.is_active = True
            user.is_verified = False
            user.created_at = datetime.now()
            user.updated_at = datetime.now()
            user.last_login = None

        mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)
        mock_db_session.add = MagicMock()

        user_create = UserCreate(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"],
        )

        registered_user = await auth_flow_service.register_user(user_create)
        assert registered_user is not None

        # Deactivate user - create proper mock User object
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = test_user_data["username"]
        mock_user.email = test_user_data["email"]
        mock_user.full_name = test_user_data["full_name"]
        mock_user.is_active = True  # Start as active
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.last_login = None
        mock_user.hashed_password = "$2b$12$3ixGaIYNNWj.flY/C43Xm.BSQxQoZ7du0MyiDviUQk9EY9r2J0D52"  # testpassword123
        mock_user.roles = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        deactivation_result = await auth_flow_service.deactivate_user(1)  # Use user ID
        assert deactivation_result is True
        assert mock_user.is_active is False

        # Try to login with deactivated user
        user_login = UserLogin(
            email=test_user_data["email"], password=test_user_data["password"]
        )

        login_result = await auth_flow_service.authenticate_user(user_login)
        assert login_result is None  # Should fail for inactive user

        # Reactivate user
        activation_result = await auth_flow_service.activate_user(1)  # Use user ID
        assert activation_result is True
        assert mock_user.is_active is True

        # Login with reactivated user
        login_result = await auth_flow_service.authenticate_user(user_login)
        assert login_result is not None  # Should succeed for active user


class TestAuthErrorHandling:
    """Test cases for authentication error handling."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session for error testing."""
        mock_session = MagicMock()
        mock_session.execute = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = MagicMock()
        return mock_session

    @pytest.fixture
    def test_user_data(self):
        """Test user data for error testing."""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        }

    @pytest.fixture
    def error_auth_service(self, mock_db_session):
        """Create AuthService for error testing."""
        return AuthService(db_session=mock_db_session)

    @pytest.mark.asyncio
    async def test_database_connection_error(
        self, error_auth_service, test_user_data, mock_db_session
    ):
        """Test handling of database connection errors."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database connection failed")

        user_create = UserCreate(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"],
        )

        # Test that error is properly handled
        with pytest.raises(ValueError, match="Error creating user"):
            await error_auth_service.register_user(user_create)

    def test_invalid_user_data(self, error_auth_service):
        """Test handling of invalid user data."""
        # Test with invalid email
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="invalid-email",
                password="password123",
                full_name="Test User",
            )

    def test_password_validation(
        self, error_auth_service, test_user_data, mock_db_session
    ):
        """Test password validation."""
        # Test with weak password
        with pytest.raises(ValidationError):
            UserCreate(
                username=test_user_data["username"],
                email=test_user_data["email"],
                password="123",  # Too short
                full_name=test_user_data["full_name"],
            )

    @pytest.mark.asyncio
    async def test_concurrent_user_creation(
        self, error_auth_service, test_user_data, mock_db_session
    ):
        """Test concurrent user creation handling."""
        # Mock database constraint violation
        mock_db_session.commit.side_effect = Exception("Unique constraint violation")

        user_create = UserCreate(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"],
        )

        # Test that constraint violation is handled
        with pytest.raises(ValueError, match="Error creating user"):
            await error_auth_service.register_user(user_create)
