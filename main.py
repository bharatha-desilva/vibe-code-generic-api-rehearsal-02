"""
FastAPI MongoDB Generic API with Authentication
This API provides dynamic entity endpoints and authentication endpoints for user management.
"""

import os
import uvicorn
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from bson import ObjectId
import jwt

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://nuwanwp:zXi15ByhNUNFEOOD@cluster0.gjas8wj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DB = "fastapi_mongo_api"

# JWT Configuration
JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI MongoDB Generic API",
    description="Generic REST API with MongoDB and Authentication",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

# Security
security = HTTPBearer()

# Pydantic Models for Authentication
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LogoutRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]

class ErrorResponse(BaseModel):
    success: bool
    message: str
    error: str

# Helper Functions
def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if key == "_id" and isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                serialized[key] = serialize_doc(value)
            else:
                serialized[key] = value
        return serialized
    return doc

def convert_query_params(params: Dict[str, str]) -> Dict[str, Any]:
    """Convert query parameters to appropriate types"""
    converted = {}
    for key, value in params.items():
        if key == "_id":
            # Don't convert _id to ObjectId to avoid errors
            converted[key] = value
        elif value.lower() == "true":
            converted[key] = True
        elif value.lower() == "false":
            converted[key] = False
        elif value.isdigit():
            converted[key] = int(value)
        else:
            try:
                converted[key] = float(value)
            except ValueError:
                converted[key] = value
    return converted

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)  # Refresh token expires in 30 days
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return {"user_id": user_id, "payload": payload}
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

def get_current_user(token_data: dict = Depends(verify_token)):
    """Get current authenticated user"""
    user_id = token_data["user_id"]
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return serialize_doc(user)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )

# Authentication Endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return tokens"""
    try:
        # Find user by email
        user = db.users.find_one({"email": login_data.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check password (plain text for now as per guidelines)
        if user.get("password") != login_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Update last login
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create tokens
        user_id = str(user["_id"])
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        # Prepare user data
        user_data = {
            "id": user_id,
            "email": user["email"],
            "name": user.get("name", ""),
            "role": user.get("role", "user")
        }
        
        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "user": user_data,
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
                }
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/logout")
async def logout(logout_data: LogoutRequest, current_user: dict = Depends(get_current_user)):
    """Logout user and invalidate tokens"""
    # In a production environment, you would typically:
    # 1. Add the tokens to a blacklist
    # 2. Store blacklisted tokens in database/cache
    # For this implementation, we'll just return success
    return {
        "success": True,
        "message": "Logout successful"
    }

@app.get("/auth/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    user_data = {
        "id": current_user["_id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "role": current_user.get("role", "user"),
        "created_at": current_user.get("created_at", "").isoformat() if current_user.get("created_at") else None,
        "updated_at": current_user.get("updated_at", "").isoformat() if current_user.get("updated_at") else None,
        "last_login": current_user.get("last_login", "").isoformat() if current_user.get("last_login") else None
    }
    
    return {
        "success": True,
        "message": "Profile retrieved successfully",
        "data": {
            "user": user_data
        }
    }

@app.post("/auth/validate")
async def validate_token(token_data: dict = Depends(verify_token)):
    """Validate token and return token status"""
    payload = token_data["payload"]
    expires_at = datetime.fromtimestamp(payload["exp"])
    
    return {
        "success": True,
        "message": "Token is valid",
        "data": {
            "valid": True,
            "user_id": token_data["user_id"],
            "expires_at": expires_at.isoformat(),
            "token_type": "access_token"
        }
    }

# Dynamic Entity Endpoints
@app.get("/{entity}")
async def get_all_documents(entity: str):
    """Get all documents from specified collection"""
    try:
        collection = db[entity]
        documents = list(collection.find({}))
        return serialize_doc(documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{entity}/id/{item_id}")
async def get_document_by_id(entity: str, item_id: str):
    """Get single document by ObjectId"""
    try:
        collection = db[entity]
        try:
            object_id = ObjectId(item_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        document = collection.find_one({"_id": object_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return serialize_doc(document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{entity}")
async def save_new_document(entity: str, document: Dict[str, Any]):
    """Save new document to collection"""
    try:
        collection = db[entity]
        
        # Add timestamps
        document["created_at"] = datetime.utcnow()
        document["updated_at"] = datetime.utcnow()
        
        result = collection.insert_one(document)
        
        # Return the saved document
        saved_document = collection.find_one({"_id": result.inserted_id})
        return serialize_doc(saved_document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/{entity}/{item_id}")
async def update_document(entity: str, item_id: str, update_data: Dict[str, Any]):
    """Update existing document by ObjectId"""
    try:
        collection = db[entity]
        try:
            object_id = ObjectId(item_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        # Add update timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        result = collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Return updated document
        updated_document = collection.find_one({"_id": object_id})
        return serialize_doc(updated_document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{entity}/filter")
async def get_filtered_documents(entity: str, request: Request):
    """Get documents filtered by query parameters"""
    try:
        collection = db[entity]
        
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Convert query parameters to appropriate types
        filters = convert_query_params(query_params)
        
        # Query the collection
        documents = list(collection.find(filters))
        return serialize_doc(documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/{entity}/{item_id}")
async def delete_document(entity: str, item_id: str):
    """Delete document by ObjectId"""
    try:
        collection = db[entity]
        try:
            object_id = ObjectId(item_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        # Get document before deletion
        document = collection.find_one({"_id": object_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete the document
        result = collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "message": "Document deleted successfully",
            "deleted_document": serialize_doc(document)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "FastAPI MongoDB Generic API",
        "version": "1.0.0",
        "endpoints": {
            "authentication": [
                "POST /auth/login",
                "POST /auth/logout", 
                "GET /auth/profile",
                "POST /auth/validate"
            ],
            "dynamic_entities": [
                "GET /{entity}",
                "GET /{entity}/id/{item_id}",
                "POST /{entity}",
                "PUT /{entity}/{item_id}",
                "GET /{entity}/filter",
                "DELETE /{entity}/{item_id}"
            ]
        }
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    if exc.status_code == 401:
        error_code = "INVALID_TOKEN"
        if "credentials" in exc.detail.lower():
            error_code = "INVALID_CREDENTIALS"
        elif "expired" in exc.detail.lower():
            error_code = "TOKEN_EXPIRED"
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "error": error_code
            }
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail
        }
    )

# Startup configuration for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
