# FastAPI MongoDB Generic API

A generic REST API built with FastAPI and MongoDB that provides dynamic entity endpoints and authentication functionality.

## Features

- **Dynamic Entity Endpoints**: Work with any collection/entity through generic REST endpoints
- **Authentication System**: Complete JWT-based authentication with login, logout, profile, and token validation
- **MongoDB Integration**: Direct JSON document storage without schema constraints
- **CORS Support**: Pre-configured for cross-origin requests
- **Automatic Serialization**: MongoDB ObjectId to string conversion
- **Dynamic Filtering**: Query any collection with URL parameters

## API Endpoints

### Authentication Endpoints

- `POST /auth/login` - User authentication
- `POST /auth/logout` - User logout (requires token)
- `GET /auth/profile` - Get user profile (requires token)
- `POST /auth/validate` - Validate JWT token

### Dynamic Entity Endpoints

- `GET /{entity}` - Get all documents from collection
- `GET /{entity}/id/{item_id}` - Get document by ObjectId
- `POST /{entity}` - Create new document
- `PUT /{entity}/{item_id}` - Update document by ObjectId
- `GET /{entity}/filter` - Get filtered documents using query parameters
- `DELETE /{entity}/{item_id}` - Delete document by ObjectId

## Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/bharatha-desilva/vibe-code-generic-api-rehearsal-02.git
   cd vibe-code-generic-api-rehearsal-02
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

5. **Access API Documentation**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Environment Variables

The following environment variables are supported:

- `PORT`: Server port (default: 8000)
- `MONGODB_URI`: MongoDB connection string (configured in code)
- `JWT_SECRET_KEY`: JWT secret key (change in production)

## Usage Examples

### Authentication

#### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "userpassword"
  }'
```

#### Get Profile
```bash
curl -X GET "http://localhost:8000/auth/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Dynamic Entity Operations

#### Create a new user
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "role": "user"
  }'
```

#### Get all users
```bash
curl -X GET "http://localhost:8000/users"
```

#### Get user by ID
```bash
curl -X GET "http://localhost:8000/users/id/507f1f77bcf86cd799439011"
```

#### Update user
```bash
curl -X PUT "http://localhost:8000/users/507f1f77bcf86cd799439011" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "role": "admin"
  }'
```

#### Filter users
```bash
curl -X GET "http://localhost:8000/users/filter?role=admin&is_active=true"
```

#### Delete user
```bash
curl -X DELETE "http://localhost:8000/users/507f1f77bcf86cd799439011"
```

## Database Schema

### Users Collection

The authentication system works with a `users` collection:

```json
{
  "_id": "ObjectId",
  "email": "string (unique)",
  "password": "string (plain text - change in production)",
  "name": "string",
  "role": "string",
  "created_at": "Date",
  "updated_at": "Date",
  "last_login": "Date",
  "is_active": "boolean",
  "email_verified": "boolean"
}
```

### Sample User Document

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "admin@example.com",
  "password": "admin123",
  "name": "Admin User",
  "role": "admin",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z",
  "is_active": true,
  "email_verified": true
}
```

## Deployment

### Deploy to Render

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create Render Service**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `fastapi-mongo-api`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python main.py`

3. **Environment Variables (Optional)**
   - Add any custom environment variables in Render dashboard
   - The app will automatically detect the `PORT` environment variable

### Deploy to Other Platforms

The application is configured to work with any platform that supports Python web applications:

- **Heroku**: Add a `Procfile` with `web: python main.py`
- **Railway**: Works out of the box with automatic port detection
- **DigitalOcean App Platform**: Configure Python environment with start command `python main.py`

## Security Notes

⚠️ **Important Security Considerations for Production:**

1. **Change JWT Secret**: Update `JWT_SECRET_KEY` to a secure random string
2. **Password Hashing**: Implement bcrypt or similar for password hashing
3. **HTTPS**: Use HTTPS in production
4. **Environment Variables**: Move sensitive config to environment variables
5. **Rate Limiting**: Implement rate limiting for authentication endpoints
6. **Token Blacklisting**: Implement proper token blacklisting for logout
7. **Input Validation**: Add comprehensive input validation
8. **Error Handling**: Don't expose sensitive information in error messages

## API Response Format

All authentication endpoints follow this response format:

**Success Response:**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error description",
  "error": "ERROR_CODE"
}
```

## Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_CREDENTIALS` | Email or password is incorrect |
| `INVALID_TOKEN` | Token is invalid, malformed, or expired |
| `TOKEN_EXPIRED` | Token has expired |
| `USER_NOT_FOUND` | User does not exist |
| `ACCOUNT_DISABLED` | User account has been disabled |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.
