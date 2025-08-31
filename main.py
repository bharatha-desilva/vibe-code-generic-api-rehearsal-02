import os
import uvicorn
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import bcrypt
import jwt
from pydantic import BaseModel

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://nuwanwp:zXi15ByhNUNFEOOD@cluster0.gjas8wj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DB = "fastapi_mongo_api"

# JWT Configuration
JWT_SECRET = "your-secret-key-here"  # In production, use environment variable
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Initialize FastAPI
app = FastAPI(title="FastAPI MongoDB API with Authentication", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

# Security
security = HTTPBearer()

# Pydantic models for authentication
class LoginRequest(BaseModel):
    email: str
    password: str

class LogoutRequest(BaseModel):
    refresh_token: str

# Helper functions
def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(user_id: str = Depends(verify_token)):
    """Get current user from database"""
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return serialize_doc(user)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )

def convert_query_params(params: Dict[str, str]) -> Dict[str, Any]:
    """Convert query parameters to appropriate types"""
    converted = {}
    for key, value in params.items():
        if key == "_id":
            # Keep _id as string to avoid ObjectId conversion issues
            converted[key] = value
        elif value.lower() == "true":
            converted[key] = True
        elif value.lower() == "false":
            converted[key] = False
        else:
            # Try to convert to number
            try:
                if "." in value:
                    converted[key] = float(value)
                else:
                    converted[key] = int(value)
            except ValueError:
                converted[key] = value
    return converted

# Authentication endpoints
@app.post("/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return tokens"""
    user = db.users.find_one({"email": request.email})
    
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"error": "INVALID_CREDENTIALS"}
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled",
            headers={"error": "ACCOUNT_DISABLED"}
        )
    
    # Update last login
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user["_id"])})
    refresh_token = create_access_token(data={"sub": str(user["_id"]), "type": "refresh"})
    
    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("name", ""),
                "role": user.get("role", "user")
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
    }

@app.post("/auth/logout")
async def logout(request: LogoutRequest, current_user: dict = Depends(get_current_user)):
    """Logout user and invalidate tokens"""
    # In a production system, you would maintain a blacklist of tokens
    # For this implementation, we'll just return success
    return {
        "success": True,
        "message": "Logout successful"
    }

@app.get("/auth/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "success": True,
        "message": "Profile retrieved successfully",
        "data": {
            "user": {
                "id": current_user["_id"],
                "email": current_user["email"],
                "name": current_user.get("name", ""),
                "role": current_user.get("role", "user"),
                "created_at": current_user.get("created_at", "").isoformat() if current_user.get("created_at") else None,
                "updated_at": current_user.get("updated_at", "").isoformat() if current_user.get("updated_at") else None,
                "last_login": current_user.get("last_login", "").isoformat() if current_user.get("last_login") else None
            }
        }
    }

@app.post("/auth/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """Validate current token"""
    return {
        "success": True,
        "message": "Token is valid",
        "data": {
            "valid": True,
            "user_id": current_user["_id"],
            "expires_at": (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat(),
            "token_type": "access_token"
        }
    }

# Dynamic CRUD endpoints
@app.get("/{entity}")
async def get_all(entity: str):
    """Get all documents from the specified collection"""
    collection = db[entity]
    documents = list(collection.find())
    return [serialize_doc(doc) for doc in documents]

@app.get("/{entity}/id/{item_id}")
async def get_by_id(entity: str, item_id: str):
    """Get a single document by its ObjectId"""
    try:
        collection = db[entity]
        document = collection.find_one({"_id": ObjectId(item_id)})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return serialize_doc(document)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

@app.post("/{entity}")
async def save_new(entity: str, document: dict):
    """Save a new document to the specified collection"""
    collection = db[entity]
    
    # Add timestamps if not present
    if "created_at" not in document:
        document["created_at"] = datetime.utcnow()
    if "updated_at" not in document:
        document["updated_at"] = datetime.utcnow()
    
    # Hash password if this is a user document with password
    if entity == "users" and "password" in document:
        document["password"] = hash_password(document["password"])
        # Set default values for user
        document.setdefault("is_active", True)
        document.setdefault("email_verified", False)
        document.setdefault("role", "user")
    
    result = collection.insert_one(document)
    document["_id"] = result.inserted_id
    return serialize_doc(document)

@app.put("/{entity}/{item_id}")
async def update(entity: str, item_id: str, update_data: dict):
    """Update an existing document by its ObjectId"""
    try:
        collection = db[entity]
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Hash password if updating user password
        if entity == "users" and "password" in update_data:
            update_data["password"] = hash_password(update_data["password"])
        
        result = collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        updated_document = collection.find_one({"_id": ObjectId(item_id)})
        return serialize_doc(updated_document)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

@app.get("/{entity}/filter")
async def get_filtered(entity: str, request):
    """Get documents filtered by query parameters"""
    collection = db[entity]
    
    # Get query parameters
    query_params = dict(request.query_params)
    
    # Convert query parameters to appropriate types
    filters = convert_query_params(query_params)
    
    # Query the collection
    documents = list(collection.find(filters))
    return [serialize_doc(doc) for doc in documents]

@app.delete("/{entity}/{item_id}")
async def delete_by_id(entity: str, item_id: str):
    """Delete a document by its ObjectId"""
    try:
        collection = db[entity]
        result = collection.delete_one({"_id": ObjectId(item_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully", "deleted_id": item_id}
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "message": "FastAPI MongoDB API with Authentication",
        "version": "1.0.0",
        "endpoints": {
            "auth": [
                "POST /auth/login",
                "POST /auth/logout",
                "GET /auth/profile",
                "POST /auth/validate"
            ],
            "dynamic_crud": [
                "GET /{entity}",
                "GET /{entity}/id/{item_id}",
                "POST /{entity}",
                "PUT /{entity}/{item_id}",
                "GET /{entity}/filter",
                "DELETE /{entity}/{item_id}"
            ]
        }
    }

# Startup for Render deployment
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
