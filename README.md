# FastAPI MongoDB Generic API with Authentication

A dynamic FastAPI REST API with MongoDB integration that supports both generic entity operations and user authentication. The API accepts any JSON objects without requiring predefined schemas and includes comprehensive authentication endpoints.

## Features

### Dynamic Entity Endpoints
- **GET_ALL**: `GET /{entity}` - Fetch all documents from any collection
- **GET_BY_ID**: `GET /{entity}/id/{item_id}` - Fetch a single document by ObjectId
- **SAVE_NEW**: `POST /{entity}` - Save any JSON object to a collection
- **UPDATE**: `PUT /{entity}/{item_id}` - Update existing document with any fields
- **GET_FILTERED**: `GET /{entity}/filter` - Dynamic filtering using query parameters
- **DELETE_BY_ID**: `DELETE /{entity}/{item_id}` - Delete document by ObjectId

### Authentication Endpoints
- **LOGIN**: `POST /auth/login` - Authenticate user and get JWT tokens
- **LOGOUT**: `POST /auth/logout` - Invalidate user session
- **PROFILE**: `GET /auth/profile` - Get current user profile
- **VALIDATE**: `POST /auth/validate` - Validate JWT token

## Technology Stack

- **FastAPI** - Modern Python web framework
- **MongoDB Atlas** - Cloud database
- **PyMongo** - MongoDB driver for Python
- **JWT** - JSON Web Tokens for authentication
- **Uvicorn** - ASGI server

## Local Development Setup

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bharatha-desilva/vibe-code-generic-api-rehearsal-02.git
   cd vibe-code-generic-api-rehearsal-02
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API Base URL: `http://localhost:8000`
   - Interactive API Documentation: `http://localhost:8000/docs`
   - Alternative Documentation: `http://localhost:8000/redoc`

## API Usage Examples

### Authentication

#### 1. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "userpassword"
  }'
```

#### 2. Access Protected Endpoints
```bash
curl -X GET "http://localhost:8000/auth/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Dynamic Entity Operations

#### 1. Create a new user
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass",
    "role": "user",
    "is_active": true
  }'
```

#### 2. Get all users
```bash
curl -X GET "http://localhost:8000/users"
```

#### 3. Get user by ID
```bash
curl -X GET "http://localhost:8000/users/id/USER_OBJECT_ID"
```

#### 4. Update user
```bash
curl -X PUT "http://localhost:8000/users/USER_OBJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'
```

#### 5. Filter users
```bash
curl -X GET "http://localhost:8000/users/filter?role=admin&is_active=true"
```

#### 6. Delete user
```bash
curl -X DELETE "http://localhost:8000/users/USER_OBJECT_ID"
```

### Working with Any Entity

The API works with any entity name. For example, to work with "products":

```bash
# Create a product
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "price": 999.99,
    "category": "electronics",
    "in_stock": true
  }'

# Get all products
curl -X GET "http://localhost:8000/products"

# Filter products by category
curl -X GET "http://localhost:8000/products/filter?category=electronics&in_stock=true"
```

## Database Configuration

The application connects to MongoDB Atlas using the following configuration:

- **Connection String**: Pre-configured for the provided cluster
- **Database Name**: `fastapi_mongo_api`
- **Collections**: Dynamic - created automatically when first used

### Users Collection Schema
```json
{
  "_id": "ObjectId",
  "email": "string (unique)",
  "password": "string (plain text for now)",
  "username": "string",
  "role": "string",
  "created_at": "Date",
  "updated_at": "Date",
  "last_login": "Date",
  "is_active": "boolean",
  "email_verified": "boolean"
}
```

## Deployment

### GitHub Repository Setup

1. **Push to GitHub**
   ```bash
   git init
   git remote add origin https://github.com/bharatha-desilva/vibe-code-generic-api-rehearsal-02.git
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git push -u origin main
   ```

### Render Deployment

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up or log in

2. **Deploy from GitHub**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository: `vibe-code-generic-api-rehearsal-02`

3. **Configure Deployment**
   - **Name**: `fastapi-mongo-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

4. **Environment Variables** (Optional)
   - Add any environment variables if needed
   - The app will use PORT from Render automatically

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy your application

### Deployment URL
After deployment, your API will be available at:
`https://your-app-name.onrender.com`

## Security Notes

- **JWT Secret**: Change `JWT_SECRET_KEY` in production
- **Password Security**: Currently using plain text passwords (as specified in guidelines)
- **HTTPS**: Render provides HTTPS automatically
- **CORS**: Currently allows all origins for development

## API Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    // Response data
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "error": "ERROR_CODE"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_CREDENTIALS` | Login credentials are incorrect |
| `INVALID_TOKEN` | JWT token is invalid or malformed |
| `TOKEN_EXPIRED` | JWT token has expired |
| `USER_NOT_FOUND` | User does not exist |
| `ACCOUNT_DISABLED` | User account is disabled |

## Development

### Project Structure
```
├── main.py           # Main FastAPI application
├── requirements.txt  # Python dependencies
├── README.md        # Project documentation
├── .gitignore       # Git ignore rules
└── .git/           # Git repository
```

### Adding New Features
1. Modify `main.py` to add new endpoints
2. Update `requirements.txt` if new dependencies are needed
3. Test locally with `python main.py`
4. Commit and push changes to GitHub
5. Render will automatically redeploy

## Support

For issues and questions:
1. Check the interactive API documentation at `/docs`
2. Review this README for common usage patterns
3. Verify MongoDB connection and collection structure
4. Check server logs for detailed error information

## License

This project is open source and available under the MIT License.
