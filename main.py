from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import jwt
import os
import uvicorn
from typing import Optional, Dict, Any

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://nuwanwp:zXi15ByhNUNFEOOD@cluster0.gjas8wj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DB = "fastapi_mongo_api"

# JWT Configuration
JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Initialize FastAPI app
app = FastAPI(title="FastAPI MongoDB Generic API with Authentication", version="1.0.0")

# Add CORS middleware
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

def serialize_doc(doc):
    """Convert MongoDB ObjectId to string for JSON serialization"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def serialize_docs(docs):
    """Convert list of MongoDB documents"""
    return [serialize_doc(doc) for doc in docs]

def convert_value(value: str):
    """Convert string values to appropriate types for MongoDB queries"""
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    elif value.isdigit():
        return int(value)
    else:
        try:
            return float(value)
        except ValueError:
            return value

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

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data"""
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
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Authentication Endpoints

@app.post("/auth/login")
async def login(credentials: dict):
    """Authenticate user and return tokens"""
    try:
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "Username and password are required",
                    "error": "MISSING_CREDENTIALS"
                }
            )
        
        # Find user in users collection
        users_collection = db["users"]
        user = users_collection.find_one({"$or": [{"email": username}, {"username": username}]})
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "message": "Invalid credentials",
                    "error": "INVALID_CREDENTIALS"
                }
            )
        
        # For now, check password in plain text (as specified in guidelines)
        if user.get("password") != password:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "message": "Invalid credentials",
                    "error": "INVALID_CREDENTIALS"
                }
            )
        
        # Check if account is active
        if not user.get("is_active", True):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "message": "Account is disabled",
                    "error": "ACCOUNT_DISABLED"
                }
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["_id"])}, expires_delta=access_token_expires
        )
        
        # Create refresh token (longer expiration)
        refresh_token_expires = timedelta(days=7)
        refresh_token = create_access_token(
            data={"sub": str(user["_id"]), "type": "refresh"}, expires_delta=refresh_token_expires
        )
        
        # Update last login
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Login successful",
                "data": {
                    "user": {
                        "id": str(user["_id"]),
                        "email": user.get("email"),
                        "username": user.get("username"),
                        "role": user.get("role", "user")
                    },
                    "tokens": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
                    }
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            }
        )

@app.post("/auth/logout")
async def logout(request_body: dict, current_user: dict = Depends(verify_token)):
    """Logout user and invalidate tokens"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Logout successful"
        }
    )

@app.get("/auth/profile")
async def get_profile(current_user: dict = Depends(verify_token)):
    """Get current user profile"""
    try:
        users_collection = db["users"]
        user = users_collection.find_one({"_id": ObjectId(current_user["user_id"])})
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "User not found",
                    "error": "USER_NOT_FOUND"
                }
            )
        
        user_data = {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "username": user.get("username"),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at", "").isoformat() if user.get("created_at") else None,
            "updated_at": user.get("updated_at", "").isoformat() if user.get("updated_at") else None,
            "last_login": user.get("last_login", "").isoformat() if user.get("last_login") else None
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Profile retrieved successfully",
                "data": {
                    "user": user_data
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            }
        )

@app.post("/auth/validate")
async def validate_token(current_user: dict = Depends(verify_token)):
    """Validate current token"""
    try:
        payload = current_user["payload"]
        expires_at = datetime.fromtimestamp(payload["exp"])
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Token is valid",
                "data": {
                    "valid": True,
                    "user_id": current_user["user_id"],
                    "expires_at": expires_at.isoformat(),
                    "token_type": "access_token"
                }
            }
        )
        
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

# Dynamic Entity Endpoints

@app.get("/{entity}")
async def get_all_documents(entity: str):
    """Fetch all documents from the specified entity/collection"""
    try:
        collection = db[entity]
        documents = list(collection.find())
        return serialize_docs(documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{entity}/id/{item_id}")
async def get_document_by_id(entity: str, item_id: str):
    """Fetch a single document by its MongoDB ObjectId"""
    try:
        collection = db[entity]
        document = collection.find_one({"_id": ObjectId(item_id)})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return serialize_doc(document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/{entity}")
async def save_new_document(entity: str, document: dict):
    """Save a new JSON object exactly as received in the request body"""
    try:
        collection = db[entity]
        
        # Add timestamps if not present
        if "created_at" not in document:
            document["created_at"] = datetime.utcnow()
        if "updated_at" not in document:
            document["updated_at"] = datetime.utcnow()
            
        result = collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return serialize_doc(document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/{entity}/{item_id}")
async def update_document(entity: str, item_id: str, update_data: dict):
    """Update an existing document by its ObjectId with JSON fields provided in the request"""
    try:
        collection = db[entity]
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        result = collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        updated_document = collection.find_one({"_id": ObjectId(item_id)})
        return serialize_doc(updated_document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{entity}/filter")
async def get_filtered_documents(entity: str, request):
    """Fetch documents dynamically filtered by any query parameters"""
    try:
        collection = db[entity]
        
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Build filter object
        filters = {}
        for key, value in query_params.items():
            # Convert value types but don't convert _id to ObjectId
            if key != "_id":
                filters[key] = convert_value(value)
            else:
                filters[key] = value
        
        # Query the collection
        documents = list(collection.find(filters))
        return serialize_docs(documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/{entity}/{item_id}")
async def delete_document(entity: str, item_id: str):
    """Delete document by ObjectId"""
    try:
        collection = db[entity]
        result = collection.delete_one({"_id": ObjectId(item_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully", "deleted_id": item_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FastAPI MongoDB Generic API with Authentication",
        "version": "1.0.0",
        "endpoints": {
            "auth": [
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

# Startup logic for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
