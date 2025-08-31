# FastAPI MongoDB API with Authentication

A dynamic REST API built with FastAPI and MongoDB that provides both generic CRUD operations for any collection and comprehensive authentication endpoints.

## Features

- **Dynamic CRUD Operations**: Perform operations on any MongoDB collection without predefined schemas
- **Authentication System**: Complete JWT-based authentication with login, logout, profile, and token validation
- **MongoDB Integration**: Direct integration with MongoDB Atlas
- **CORS Support**: Full CORS middleware for cross-origin requests
- **Automatic Type Conversion**: Smart query parameter conversion for filtering
- **Password Security**: bcrypt password hashing
- **Token Management**: JWT access and refresh tokens

## API Endpoints

### Authentication Endpoints (`/auth`)

- `POST /auth/login` - User login with email/password
- `POST /auth/logout` - Logout and invalidate tokens
- `GET /auth/profile` - Get current user profile (requires auth)
- `POST /auth/validate` - Validate current token (requires auth)

### Dynamic CRUD Endpoints (`/{entity}`)

- `GET /{entity}` - Get all documents from collection
- `GET /{entity}/id/{item_id}` - Get document by ObjectId
- `POST /{entity}` - Create new document
- `PUT /{entity}/{item_id}` - Update document by ObjectId
- `GET /{entity}/filter` - Get filtered documents using query parameters
- `DELETE /{entity}/{item_id}` - Delete document by ObjectId

## Installation & Setup

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB)
- Git

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bharatha-desilva/vibe-code-generic-api-rehearsal-02.git
   cd vibe-code-generic-api-rehearsal-02
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

5. **View API documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Database Setup

The API uses MongoDB Atlas with the following configuration:
- Database: `fastapi_mongo_api`
- Collections: Dynamic (created as needed)
- Special collection: `users` (for authentication)

### User Collection Schema

```json
{
  "_id": "ObjectId",
  "email": "string (unique)",
  "password": "string (hashed with bcrypt)",
  "name": "string",
  "role": "string (default: 'user')",
  "created_at": "Date",
  "updated_at": "Date",
  "last_login": "Date",
  "is_active": "boolean (default: true)",
  "email_verified": "boolean (default: false)"
}
```

## Usage Examples

### Authentication

1. **Create a user (using dynamic endpoint):**
   ```bash
   curl -X POST "http://localhost:8000/users" \
   -H "Content-Type: application/json" \
   -d '{
     "email": "user@example.com",
     "password": "securepassword",
     "name": "John Doe",
     "role": "user"
   }'
   ```

2. **Login:**
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
   -H "Content-Type: application/json" \
   -d '{
     "email": "user@example.com",
     "password": "securepassword"
   }'
   ```

3. **Access protected endpoints:**
   ```bash
   curl -X GET "http://localhost:8000/auth/profile" \
   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Dynamic CRUD Operations

1. **Create documents in any collection:**
   ```bash
   # Create a product
   curl -X POST "http://localhost:8000/products" \
   -H "Content-Type: application/json" \
   -d '{
     "name": "Laptop",
     "price": 999.99,
     "category": "Electronics"
   }'
   
   # Create a blog post
   curl -X POST "http://localhost:8000/posts" \
   -H "Content-Type: application/json" \
   -d '{
     "title": "My First Post",
     "content": "Hello World!",
     "author": "John Doe"
   }'
   ```

2. **Filter documents:**
   ```bash
   # Filter products by category
   curl "http://localhost:8000/products/filter?category=Electronics"
   
   # Filter with multiple parameters
   curl "http://localhost:8000/products/filter?category=Electronics&price=999.99"
   ```

## Deployment

### Deploy to Render

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render:**
   - Go to [Render.com](https://render.com)
   - Connect your GitHub repository
   - Create a new Web Service
   - Use the following settings:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python main.py`
     - **Environment:** Python 3

3. **Environment Variables (Optional):**
   - `JWT_SECRET`: Your JWT secret key
   - `PORT`: Port number (Render sets this automatically)

### Deploy to Other Platforms

The application is configured to work with any platform that supports Python web applications:

- **Heroku**: Add a `Procfile` with `web: python main.py`
- **Railway**: Works out of the box
- **DigitalOcean App Platform**: Uses the existing configuration
- **AWS/GCP/Azure**: Deploy as a containerized application

## Configuration

### Environment Variables

- `PORT`: Server port (default: 8000)
- `JWT_SECRET`: Secret key for JWT tokens (update in production)
- `MONGODB_URI`: MongoDB connection string (currently hardcoded)

### Security Notes

- Change the JWT secret in production
- Use environment variables for sensitive configuration
- Implement rate limiting for authentication endpoints
- Consider implementing refresh token rotation
- Use HTTPS in production

## API Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
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

## Development

### Code Structure

- `main.py` - Main application file with all endpoints
- `requirements.txt` - Python dependencies
- `README.md` - Documentation
- `.gitignore` - Git ignore rules

### Key Features

- **Dynamic Collections**: No need to predefine schemas
- **Automatic Serialization**: MongoDB ObjectId to string conversion
- **Type Conversion**: Smart query parameter type detection
- **Password Security**: bcrypt hashing for user passwords
- **Token Management**: JWT with configurable expiration
- **CORS Ready**: Configured for cross-origin requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.
