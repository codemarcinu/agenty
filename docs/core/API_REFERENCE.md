# 🔧 API Reference - FoodSave AI

## 📋 Overview

The FoodSave AI API is a RESTful service built with FastAPI that provides endpoints for interacting with the multi-agent AI system. The API supports real-time chat, file uploads, RAG operations, weather data, concise responses, and system monitoring.

## 🔗 Base URL

- **Development**: `http://localhost:8001`
- **Production**: `https://api.foodsave-ai.com`

## 📚 API Versioning

The API uses URL-based versioning:
- **v1**: Legacy endpoints (deprecated)
- **v2**: Current stable endpoints (recommended)

## 🔐 Authentication

The API uses JWT-based authentication for protected endpoints. All authentication endpoints are available without authentication.

### Authentication Flow

1. **Register**: `POST /auth/register` - Create new user account
2. **Login**: `POST /auth/login` - Get access and refresh tokens
3. **Protected Endpoints**: Include `Authorization: Bearer <token>` header
4. **Refresh**: `POST /auth/refresh` - Get new access token
5. **Logout**: `POST /auth/logout` - Invalidate tokens

## 📊 Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "error description"
    }
  },
  "timestamp": "2024-12-21T10:30:00Z"
}
```

## 🔐 Authentication Endpoints

### POST `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "username": "username",
  "full_name": "Full Name"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-12-21T10:30:00Z",
  "updated_at": "2024-12-21T10:30:00Z",
  "last_login": null,
  "roles": []
}
```

### POST `/auth/login`

Login and get access tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-12-21T10:30:00Z",
    "updated_at": "2024-12-21T10:30:00Z",
    "last_login": "2024-12-21T10:30:00Z",
    "roles": ["user"]
  }
}
```

### GET `/auth/me`

Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-12-21T10:30:00Z",
  "updated_at": "2024-12-21T10:30:00Z",
  "last_login": "2024-12-21T10:30:00Z",
  "roles": ["user"]
}
```

### POST `/auth/refresh`

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-12-21T10:30:00Z",
    "updated_at": "2024-12-21T10:30:00Z",
    "last_login": "2024-12-21T10:30:00Z",
    "roles": ["user"]
  }
}
```

### POST `/auth/logout`

Logout and invalidate tokens (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

## 🗣️ Chat API

### POST `/api/v1/chat`

Main endpoint for interacting with AI agents.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What can I cook with chicken and rice?",
  "session_id": "user_123_session_456",
  "context": {
    "user_preferences": {
      "diet": "vegetarian",
      "allergies": ["nuts", "shellfish"]
    },
    "available_ingredients": ["chicken", "rice", "onions"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "You can make a delicious chicken and rice dish! Here are some ideas...",
    "session_id": "user_123_session_456",
    "agent_used": "cooking_assistant",
    "confidence": 0.95,
    "processing_time": 1.2
  },
  "message": "Response generated successfully",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

## 📸 Receipt Analysis API

### POST `/api/v2/receipts/upload`

Upload and analyze a receipt image.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
```
file: [receipt_image.jpg]
```

**Response:**
```json
{
  "success": true,
  "data": {
    "store_name": "BIEDRONKA",
    "normalized_store_name": "Biedronka",
    "store_chain": "Biedronka",
    "store_type": "discount_store",
    "date": "2024-12-21T10:30:00Z",
    "items": [
      {
        "name": "Mleko 3.2% 1L",
        "normalized_name": "Mleko 3.2% 1L",
        "quantity": 1.0,
        "unit_price": 4.99,
        "total_price": 4.99,
        "category": "Nabiał > Mleko i śmietana",
        "category_en": "Dairy Products > Milk & Cream",
        "category_confidence": 0.9,
        "category_method": "bielik_ai"
      }
    ],
    "total_amount": 4.99,
    "vat_amount": 0.87,
    "processing_time": 2.1
  },
  "message": "Receipt analyzed successfully",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

### POST `/api/v2/receipts/analyze`

Analyze receipt text (for pre-processed OCR text).

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "ocr_text": "BIEDRONKA\nMleko 3.2% 1L x 4.99\nRazem: 4.99",
  "user_id": 1
}
```

## 📚 RAG (Retrieval-Augmented Generation) API

### POST `/api/v2/rag/query`

Query the RAG system with documents.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "What are the best practices for food storage?",
  "filters": {
    "category": "food_safety",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  },
  "max_results": 5
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "answer": "Based on the documents, here are the best practices...",
    "sources": [
      {
        "title": "Food Storage Guidelines",
        "content": "Keep food at proper temperatures...",
        "similarity_score": 0.95
      }
    ],
    "processing_time": 1.8
  },
  "message": "RAG query completed successfully",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

## 🌤️ Weather API

### GET `/api/v2/weather/current`

Get current weather information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `city` (string): City name
- `country` (string): Country code (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "city": "Warsaw",
    "country": "PL",
    "temperature": 15.5,
    "humidity": 65,
    "description": "Partly cloudy",
    "icon": "02d",
    "timestamp": "2024-12-21T10:30:00Z"
  },
  "message": "Weather data retrieved successfully",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

## 📊 Monitoring API

### GET `/health`

Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

### GET `/monitoring/status`

Get detailed system status (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "status": "healthy",
      "uptime": 3600,
      "version": "1.0.0"
    },
    "database": {
      "status": "connected",
      "connections": 5,
      "response_time": 0.05
    },
    "ai_models": {
      "bielik_4_5b": "loaded",
      "bielik_11b": "loaded",
      "response_time": 1.2
    },
    "agents": {
      "total": 38,
      "active": 35,
      "health": "healthy"
    }
  },
  "message": "System status retrieved successfully",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

## 🔍 Search API

### GET `/api/v2/search`

Search across conversations and documents.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `q` (string): Search query
- `type` (string): Search type (conversations, documents, all)
- `limit` (integer): Maximum results (default: 10)
- `offset` (integer): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "conv_123",
        "type": "conversation",
        "title": "Cooking discussion",
        "content": "What can I cook with chicken and rice?",
        "timestamp": "2024-12-21T10:30:00Z",
        "relevance_score": 0.95
      }
    ],
    "total": 1,
    "processing_time": 0.8
  },
  "message": "Search completed successfully",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

## 🚨 Error Codes

### HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **500**: Internal Server Error

### Error Codes

- **AUTH_INVALID_CREDENTIALS**: Invalid email or password
- **AUTH_USER_NOT_FOUND**: User not found
- **AUTH_USER_DISABLED**: User account is disabled
- **AUTH_TOKEN_EXPIRED**: Access token expired
- **AUTH_TOKEN_INVALID**: Invalid token
- **VALIDATION_ERROR**: Input validation failed
- **FILE_TOO_LARGE**: Uploaded file is too large
- **UNSUPPORTED_FILE_TYPE**: File type not supported
- **AI_MODEL_UNAVAILABLE**: AI model not available
- **DATABASE_ERROR**: Database operation failed

## 📝 Testing

### Test Authentication

```bash
# Register new user
curl -X POST "http://localhost:8001/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "username": "testuser",
    "full_name": "Test User"
  }'

# Login
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Get user info (replace YOUR_TOKEN with actual token)
curl -X GET "http://localhost:8001/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Health Check

```bash
curl http://localhost:8001/health
```

### Test Chat API

```bash
# Replace YOUR_TOKEN with actual token
curl -X POST "http://localhost:8001/api/v1/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "session_id": "test_session_123"
  }'
```

## 📚 Additional Resources

- **Interactive API Docs**: http://localhost:8001/docs
- **ReDoc Documentation**: http://localhost:8001/redoc
- **OpenAPI Schema**: http://localhost:8001/openapi.json
- **Health Check**: http://localhost:8001/health

---

## 🔄 Recent Updates

### 2025-07-07 - Authentication Fixes
- ✅ Fixed async/greenlet issues with SQLAlchemy
- ✅ Implemented eager loading for user roles
- ✅ Fixed type conversion issues
- ✅ Added automatic role assignments
- ✅ Created authentication test script

### 2025-07-06 - Docker Optimization
- ✅ Optimized Dockerfile with multi-stage builds
- ✅ Added health checks for all services
- ✅ Created .dockerignore for minimal build context
- ✅ Added build-all-optimized.sh script
