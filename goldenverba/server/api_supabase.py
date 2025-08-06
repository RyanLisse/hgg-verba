"""FastAPI server with Supabase integration."""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from goldenverba.components.supabase_manager import SupabaseManager
from goldenverba.components.types import Document, Chunk


app = FastAPI(title="Verba API with Supabase", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase manager
supabase_manager: Optional[SupabaseManager] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_cache: bool = True
    stream: bool = True


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.7
    search_type: str = "hybrid"  # "vector", "hybrid", or "text"
    alpha: float = 0.5  # Weight for hybrid search


class DocumentUpload(BaseModel):
    name: str
    content: str
    type: str
    metadata: Dict[str, Any] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize Supabase connection on startup."""
    global supabase_manager
    supabase_manager = SupabaseManager()
    await supabase_manager.initialize()
    print("Supabase connection initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Supabase connection on shutdown."""
    if supabase_manager:
        await supabase_manager.close()
    print("Supabase connection closed")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Verba API with Supabase",
        "version": "2.0.0",
        "database": "Supabase with pgvector"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        docs = await supabase_manager.get_documents(limit=1)
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    metadata: str = Form("{}")
):
    """Upload and process a document."""
    try:
        # Read file content
        content = await file.read()
        
        # Parse metadata
        meta = json.loads(metadata) if metadata else {}
        
        # Create document
        doc = Document(
            name=file.filename,
            type=file.filename.split(".")[-1].upper(),
            content=content.decode("utf-8") if isinstance(content, bytes) else content,
            metadata=meta,
            path=file.filename
        )
        
        # Insert document
        doc_id = await supabase_manager.insert_document(doc)
        
        # TODO: Process chunks and embeddings
        # This would involve:
        # 1. Chunking the document
        # 2. Creating embeddings
        # 3. Storing chunks with embeddings
        
        return {
            "success": True,
            "document_id": doc_id,
            "message": f"Document {file.filename} uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def get_documents(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get list of documents."""
    try:
        documents = await supabase_manager.get_documents(status, limit, offset)
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks."""
    try:
        success = await supabase_manager.delete_document(document_id)
        if success:
            return {"success": True, "message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search(request: SearchRequest):
    """Search for documents using vector similarity."""
    try:
        # TODO: Generate embedding for query
        # For now, using a placeholder embedding
        query_embedding = [0.1] * 1536  # Placeholder
        
        if request.search_type == "vector":
            results = await supabase_manager.vector_search(
                query_embedding=query_embedding,
                limit=request.limit,
                threshold=request.threshold
            )
        elif request.search_type == "hybrid":
            results = await supabase_manager.hybrid_search(
                query_text=request.query,
                query_embedding=query_embedding,
                limit=request.limit,
                alpha=request.alpha
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results),
            "search_type": request.search_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with RAG capabilities."""
    try:
        # Create or get conversation
        if not request.conversation_id:
            conversation = await supabase_manager.client.table("conversations").insert({
                "title": f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }).execute()
            conversation_id = conversation.data[0]["id"]
        else:
            conversation_id = request.conversation_id
        
        # Add user message
        await supabase_manager.client.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "user",
            "content": request.message
        }).execute()
        
        # TODO: Generate embedding for query
        query_embedding = [0.1] * 1536  # Placeholder
        
        # Check cache if enabled
        if request.use_cache:
            cached = await supabase_manager.search_cache(query_embedding)
            if cached:
                # Add cached response as assistant message
                await supabase_manager.client.table("messages").insert({
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": cached["response"]
                }).execute()
                
                return {
                    "conversation_id": conversation_id,
                    "response": cached["response"],
                    "cached": True
                }
        
        # Search for relevant chunks
        chunks = await supabase_manager.hybrid_search(
            query_text=request.message,
            query_embedding=query_embedding,
            limit=5,
            alpha=0.7
        )
        
        # TODO: Generate response using LLM with context from chunks
        # For now, returning a placeholder response
        response = f"I found {len(chunks)} relevant documents for your query: '{request.message}'"
        
        # Store in cache
        await supabase_manager.add_to_cache(
            query=request.message,
            query_embedding=query_embedding,
            response=response
        )
        
        # Add assistant message
        await supabase_manager.client.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": response,
            "chunk_ids": [chunk["id"] for chunk in chunks]
        }).execute()
        
        # Add to suggestions
        await supabase_manager.add_suggestion(request.message)
        
        return {
            "conversation_id": conversation_id,
            "response": response,
            "chunks": chunks,
            "cached": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get all messages for a conversation."""
    try:
        messages = await supabase_manager.client.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at").execute()
        
        return {
            "conversation_id": conversation_id,
            "messages": messages.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/suggestions")
async def get_suggestions(prefix: str, limit: int = 10):
    """Get query suggestions based on prefix."""
    try:
        suggestions = await supabase_manager.get_suggestions(prefix, limit)
        return {
            "prefix": prefix,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config")
async def save_configuration(
    config_type: str,
    config_name: str,
    config_data: Dict[str, Any],
    set_active: bool = False
):
    """Save configuration."""
    try:
        config_id = await supabase_manager.save_configuration(
            config_type=config_type,
            config_name=config_name,
            config_data=config_data,
            set_active=set_active
        )
        return {
            "success": True,
            "config_id": config_id,
            "message": "Configuration saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/{config_type}")
async def get_configuration(config_type: str, config_name: Optional[str] = None):
    """Get configuration."""
    try:
        config = await supabase_manager.get_configuration(config_type, config_name)
        if config:
            return {
                "config_type": config_type,
                "config_name": config_name,
                "data": config
            }
        else:
            raise HTTPException(status_code=404, detail="Configuration not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "search":
                # Perform search and send results
                query_embedding = [0.1] * 1536  # Placeholder
                results = await supabase_manager.vector_search(
                    query_embedding=query_embedding,
                    limit=5
                )
                await websocket.send_json({
                    "type": "search_results",
                    "results": results
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Unknown message type"
                })
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)