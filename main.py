from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timedelta
import jwt
import os
import uvicorn
from typing import Dict, Any, Optional

# MongoDB configuration
MONGODB_URI = "mongodb+srv://nuwanwp:zXi15ByhNUNFEOOD@cluster0.gjas8wj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DB = "fastapi_mongo_api"

# JWT configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI MongoDB Dynamic API with Authentication",
    description="Dynamic REST API with MongoDB and JWT Authentication",
    version="1.0.0"
)

# CORS middleware
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

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    if isinstance(doc, dict) and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
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

def convert_query_params(params: dict) -> dict:
    """Convert query parameters to appropriate types"""
    converted = {}
    for key, value in params.items():
        if key == "_id":
            # Don't convert _id to ObjectId to avoid Invalid ObjectId errors
            converted[key] = value
        elif value.lower() == "true":
            converted[key] = True
        elif value.lower() == "false":
            converted[key] = False
        elif value.isdigit():
            converted[key] = int(value)
        elif value.replace(".", "", 1).isdigit():
            converted[key] = float(value)
        else:
            converted[key] = value
    return converted

# Authentication endpoints
@app.post("/auth/login")
async def login(request: Request):
    """Authenticate user and return tokens"""
    try:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
        
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )
        
        # Find user in users collection
        users_collection = db["users"]
        user = users_collection.find_one({"username": username})
        
        if not user:
            # Try finding by email
            user = users_collection.find_one({"email": username})
        
        if not user or user.get("password") != password:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "message": "Invalid credentials",
                    "error": "INVALID_CREDENTIALS"
                }
            )
        
        # Update last login
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create tokens
        user_id = str(user["_id"])
        access_token = create_access_token(user_id)
        refresh_token = create_access_token(user_id)  # Simplified - same token for demo
        
        # Serialize user data
        user_data = serialize_doc(user)
        user_data.pop("password", None)  # Remove password from response
        
        response = JSONResponse(content={
            "success": True,
            "message": "Login successful",
            "data": {
                "user": {
                    "id": user_data["_id"],
                    "email": user_data.get("email", ""),
                    "username": user_data.get("username", ""),
                    "role": user_data.get("role", "user")
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": JWT_EXPIRATION_HOURS * 3600
                }
            }
        })
        
        # Set HttpOnly cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/auth/logout")
async def logout(user_id: str = Depends(verify_token)):
    """Logout user and invalidate tokens"""
    try:
        response = JSONResponse(content={
            "success": True,
            "message": "Logout successful"
        })
        
        # Clear the HttpOnly cookie
        response.delete_cookie(key="access_token")
        
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "Invalid or expired token",
                "error": "INVALID_TOKEN"
            }
        )

@app.get("/auth/profile")
async def get_profile(user_id: str = Depends(verify_token)):
    """Get current user profile"""
    try:
        users_collection = db["users"]
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "User not found",
                    "error": "USER_NOT_FOUND"
                }
            )
        
        user_data = serialize_doc(user)
        user_data.pop("password", None)  # Remove password from response
        
        return {
            "success": True,
            "message": "Profile retrieved successfully",
            "data": {
                "user": {
                    "id": user_data["_id"],
                    "email": user_data.get("email", ""),
                    "username": user_data.get("username", ""),
                    "role": user_data.get("role", "user"),
                    "created_at": user_data.get("created_at", ""),
                    "updated_at": user_data.get("updated_at", ""),
                    "last_login": user_data.get("last_login", "")
                }
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "Invalid or expired token",
                "error": "INVALID_TOKEN"
            }
        )

@app.get("/auth/validate")
async def validate_token(user_id: str = Depends(verify_token)):
    """Validate current token"""
    try:
        users_collection = db["users"]
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "message": "Invalid or expired token",
                    "data": {
                        "valid": False,
                        "error": "USER_NOT_FOUND"
                    }
                }
            )
        
        expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        return {
            "success": True,
            "message": "Token is valid",
            "data": {
                "valid": True,
                "user_id": user_id,
                "expires_at": expiration.isoformat() + "Z",
                "token_type": "access_token"
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": "Invalid or expired token",
                "data": {
                    "valid": False,
                    "error": "TOKEN_EXPIRED"
                }
            }
        )

# Dynamic CRUD endpoints
@app.get("/{entity}")
async def get_all_documents(entity: str):
    """Get all documents from a collection"""
    try:
        collection = db[entity]
        documents = list(collection.find())
        serialized_docs = [serialize_doc(doc) for doc in documents]
        return {"data": serialized_docs, "count": len(serialized_docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")

@app.get("/{entity}/id/{item_id}")
async def get_document_by_id(entity: str, item_id: str):
    """Get a single document by ID"""
    try:
        collection = db[entity]
        try:
            object_id = ObjectId(item_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        document = collection.find_one({"_id": object_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return serialize_doc(document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document: {str(e)}")

@app.post("/{entity}")
async def save_new_document(entity: str, request: Request):
    """Save a new document"""
    try:
        collection = db[entity]
        document = await request.json()
        
        # Add timestamps
        document["created_at"] = datetime.utcnow()
        document["updated_at"] = datetime.utcnow()
        
        result = collection.insert_one(document)
        document["_id"] = result.inserted_id
        
        return serialize_doc(document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving document: {str(e)}")

@app.put("/{entity}/{item_id}")
async def update_document(entity: str, item_id: str, request: Request):
    """Update a document by ID"""
    try:
        collection = db[entity]
        try:
            object_id = ObjectId(item_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        update_data = await request.json()
        update_data["updated_at"] = datetime.utcnow()
        
        result = collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        updated_document = collection.find_one({"_id": object_id})
        return serialize_doc(updated_document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

@app.get("/{entity}/filter")
async def get_filtered_documents(entity: str, request: Request):
    """Get documents with dynamic filtering"""
    try:
        collection = db[entity]
        query_params = dict(request.query_params)
        
        if not query_params:
            # If no filters, return all documents
            documents = list(collection.find())
        else:
            # Convert query parameters to appropriate types
            filters = convert_query_params(query_params)
            documents = list(collection.find(filters))
        
        serialized_docs = [serialize_doc(doc) for doc in documents]
        return {"data": serialized_docs, "count": len(serialized_docs), "filters": query_params}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering documents: {str(e)}")

@app.delete("/{entity}/{item_id}")
async def delete_document(entity: str, item_id: str):
    """Delete a document by ID"""
    try:
        collection = db[entity]
        try:
            object_id = ObjectId(item_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        # Get the document before deleting to return it
        document = collection.find_one({"_id": object_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        result = collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully", "deleted_document": serialize_doc(document)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "FastAPI MongoDB Dynamic API with Authentication",
        "version": "1.0.0",
        "endpoints": {
            "authentication": {
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "profile": "GET /auth/profile",
                "validate": "GET /auth/validate"
            },
            "dynamic_crud": {
                "get_all": "GET /{entity}",
                "get_by_id": "GET /{entity}/id/{item_id}",
                "create": "POST /{entity}",
                "update": "PUT /{entity}/{item_id}",
                "filter": "GET /{entity}/filter",
                "delete": "DELETE /{entity}/{item_id}"
            }
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.command("ping")
        return {"status": "healthy", "database": "connected", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e), "timestamp": datetime.utcnow().isoformat()}

# Startup configuration for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
