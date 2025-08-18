# User Management API Documentation

## Overview

The User Management API provides a comprehensive set of endpoints for managing user accounts, authentication, and user profiles. This RESTful API follows standard HTTP conventions and returns JSON responses.

**Base URL:** `https://api.example.com/v1`

**Authentication:** All endpoints require API key authentication via the `X-API-Key` header.

## Endpoints

### Users Collection

#### GET /users

Retrieve a list of all users with optional filtering and pagination.

**Parameters:**
- `limit` (query, integer, optional): Number of users to return (default: 20, max: 100)
- `offset` (query, integer, optional): Number of users to skip (default: 0)
- `status` (query, string, optional): Filter by user status (`active`, `inactive`, `pending`)
- `role` (query, string, optional): Filter by user role (`admin`, `user`, `moderator`)

**Response:**
```json
{
  "users": [
    {
      "id": "123",
      "username": "johndoe",
      "email": "john@example.com",
      "status": "active",
      "role": "user",
      "created_at": "2023-01-15T10:30:00Z",
      "updated_at": "2023-01-20T14:45:00Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Server error

#### POST /users

Create a new user account.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123",
  "role": "user",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
  }
}
```

**Response:**
```json
{
  "id": "456",
  "username": "newuser",
  "email": "newuser@example.com",
  "status": "pending",
  "role": "user",
  "created_at": "2023-01-25T09:15:00Z"
}
```

**Status Codes:**
- `201 Created`: User created successfully
- `400 Bad Request`: Invalid input data
- `409 Conflict`: Username or email already exists
- `422 Unprocessable Entity`: Validation errors

### Individual User Operations

#### GET /users/{id}

Retrieve detailed information about a specific user.

**Parameters:**
- `id` (path, string, required): User ID

**Response:**
```json
{
  "id": "123",
  "username": "johndoe",
  "email": "john@example.com",
  "status": "active",
  "role": "user",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "avatar_url": "https://example.com/avatars/123.jpg"
  },
  "created_at": "2023-01-15T10:30:00Z",
  "updated_at": "2023-01-20T14:45:00Z",
  "last_login": "2023-01-25T08:20:00Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: User not found
- `401 Unauthorized`: Missing or invalid API key

#### PUT /users/{id}

Update an existing user's information.

**Parameters:**
- `id` (path, string, required): User ID

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "status": "active",
  "role": "moderator",
  "profile": {
    "first_name": "John",
    "last_name": "Smith",
    "phone": "+1987654321"
  }
}
```

**Response:**
```json
{
  "id": "123",
  "username": "johndoe",
  "email": "newemail@example.com",
  "status": "active",
  "role": "moderator",
  "updated_at": "2023-01-25T16:30:00Z"
}
```

**Status Codes:**
- `200 OK`: User updated successfully
- `400 Bad Request`: Invalid input data
- `404 Not Found`: User not found
- `409 Conflict`: Email already exists

#### DELETE /users/{id}

Delete a user account.

**Parameters:**
- `id` (path, string, required): User ID

**Response:**
```json
{
  "message": "User deleted successfully",
  "deleted_at": "2023-01-25T17:45:00Z"
}
```

**Status Codes:**
- `200 OK`: User deleted successfully
- `404 Not Found`: User not found
- `403 Forbidden`: Cannot delete admin users

### Authentication Endpoints

#### POST /auth/login

Authenticate a user and return an access token.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "userpassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "123",
    "username": "johndoe",
    "role": "user"
  }
}
```

**Status Codes:**
- `200 OK`: Authentication successful
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded

#### POST /auth/logout

Logout a user and invalidate their access token.

**Headers:**
- `Authorization: Bearer {access_token}`

**Response:**
```json
{
  "message": "Logout successful"
}
```

**Status Codes:**
- `200 OK`: Logout successful
- `401 Unauthorized`: Invalid or expired token

## Error Handling

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Standard endpoints**: 100 requests per minute per API key
- **Authentication endpoints**: 10 requests per minute per IP address

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Pagination

List endpoints support cursor-based pagination:
- Use `limit` parameter to control page size (max 100)
- Use `offset` parameter to skip items
- Response includes `total` count and pagination metadata

## Data Validation

All input data is validated according to the following rules:
- **Username**: 3-50 characters, alphanumeric and underscores only
- **Email**: Valid email format, max 255 characters
- **Password**: Minimum 8 characters, must include letters and numbers
- **Phone**: Valid international phone number format

## Security Considerations

- All endpoints require HTTPS
- API keys must be kept secure and rotated regularly
- Passwords are hashed using bcrypt
- Sensitive data is never logged or cached
- Input validation prevents injection attacks
