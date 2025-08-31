# FastAPI MongoDB Dynamic API with Authentication

A dynamic REST API built with FastAPI and MongoDB that provides both CRUD operations for any entity/collection and JWT-based authentication.

## Features

### Dynamic CRUD Operations
- **GET All**: `GET /{entity}` - Fetch all documents from any collection
- **GET By ID**: `GET /{entity}/id/{item_id}` - Fetch single document by MongoDB ObjectId
- **CREATE**: `POST /{entity}` - Save new JSON object to any collection
- **UPDATE**: `PUT /{entity}/{item_id}` - Update existing document by ObjectId
- **FILTER**: `GET /{entity}/filter` - Dynamic filtering using query parameters
- **DELETE**: `DELETE /{entity}/{item_id}` - Delete document by ObjectId

### Authentication System
- **Login**: `POST /auth/login` - Authenticate and receive JWT tokens
- **Logout**: `POST /auth/logout` - Invalidate tokens and clear cookies
- **Profile**: `GET /auth/profile` - Get current user profile (protected)
- **Validate**: `GET /auth/validate` - Validate current JWT token

### Additional Features
- **CORS enabled** for all origins, headers, and methods
- **Automatic type conversion** for query parameters (strings, numbers, booleans)
- **MongoDB ObjectId serialization** to strings in responses
- **JWT authentication** with HttpOnly cookies
- **Health check** endpoint at `/health`
- **Automatic timestamps** (created_at, updated_at) for documents

## Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB instance)
- Git

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/bharatha-desilva/vibe-code-generic-api-rehearsal-02.git
cd vibe-code-generic-api-rehearsal-02
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)

The API is pre-configured with MongoDB Atlas credentials. To use your own database:

1. Update the MongoDB connection string in `main.py`:
```python
MONGODB_URI = "your-mongodb-connection-string"
MONGODB_DB = "your-database-name"
```

2. Update the JWT secret (recommended for production):
```python
JWT_SECRET = "your-secure-secret-key"
```

### 5. Run the Application

```bash
# Development server with auto-reload
uvicorn main:app --reload

# Or run directly
python main.py
```

The API will be available at: `http://localhost:8000`

### 6. API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Usage Examples

### Authentication

#### 1. Create a Test User (using dynamic API)
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword",
    "role": "user"
  }'
```

#### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword"
  }'
```

#### 3. Access Protected Endpoint
```bash
curl -X GET "http://localhost:8000/auth/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Dynamic CRUD Operations

#### 1. Create Documents
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

# Create a blog post
curl -X POST "http://localhost:8000/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "Hello world!",
    "author": "John Doe",
    "published": false
  }'
```

#### 2. Get All Documents
```bash
# Get all products
curl -X GET "http://localhost:8000/products"

# Get all posts
curl -X GET "http://localhost:8000/posts"
```

#### 3. Filter Documents
```bash
# Filter products by category and stock status
curl -X GET "http://localhost:8000/products/filter?category=electronics&in_stock=true"

# Filter posts by author
curl -X GET "http://localhost:8000/posts/filter?author=John%20Doe"
```

#### 4. Get Document by ID
```bash
curl -X GET "http://localhost:8000/products/id/OBJECT_ID_HERE"
```

#### 5. Update Document
```bash
curl -X PUT "http://localhost:8000/products/OBJECT_ID_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 899.99,
    "in_stock": false
  }'
```

#### 6. Delete Document
```bash
curl -X DELETE "http://localhost:8000/products/OBJECT_ID_HERE"
```

## Database Schema

### Users Collection
The authentication system expects a `users` collection with the following structure:

```json
{
  "_id": "ObjectId",
  "email": "string (unique)",
  "password": "string (plain text for demo - hash in production)",
  "username": "string",
  "role": "string",
  "created_at": "Date",
  "updated_at": "Date",
  "last_login": "Date",
  "is_active": "boolean",
  "email_verified": "boolean"
}
```

### Dynamic Collections
Any other collection can be created dynamically by making requests to `/{entity}` endpoints.

## Deployment on Render

### 1. Push to GitHub

Ensure your code is pushed to the GitHub repository:

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Deploy on Render

1. Go to [Render.com](https://render.com) and sign up/login
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository: `https://github.com/bharatha-desilva/vibe-code-generic-api-rehearsal-02.git`
4. Configure the service:
   - **Name**: `fastapi-mongo-api` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. Click "Create Web Service"

### 3. Environment Variables (Optional)

If you want to use environment variables for sensitive data:

- `MONGODB_URI`: Your MongoDB connection string
- `JWT_SECRET`: Your JWT secret key
- `PORT`: Port number (Render sets this automatically)

## API Endpoints Reference

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/login` | User login | No |
| POST | `/auth/logout` | User logout | Yes |
| GET | `/auth/profile` | Get user profile | Yes |
| GET | `/auth/validate` | Validate token | Yes |

### Dynamic CRUD Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/{entity}` | Get all documents | No |
| GET | `/{entity}/id/{item_id}` | Get document by ID | No |
| POST | `/{entity}` | Create new document | No |
| PUT | `/{entity}/{item_id}` | Update document | No |
| GET | `/{entity}/filter` | Filter documents | No |
| DELETE | `/{entity}/{item_id}` | Delete document | No |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc documentation |

## Security Notes

⚠️ **Important for Production:**

1. **Change JWT Secret**: Update `JWT_SECRET` to a secure, random string
2. **Hash Passwords**: Currently using plain text passwords for demo - implement bcrypt hashing
3. **HTTPS**: Enable HTTPS and set `secure=True` for cookies
4. **CORS**: Restrict CORS origins to your frontend domains
5. **Rate Limiting**: Implement rate limiting for authentication endpoints
6. **Input Validation**: Add proper input validation and sanitization
7. **Environment Variables**: Move sensitive configurations to environment variables

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and commit: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on the GitHub repository.
