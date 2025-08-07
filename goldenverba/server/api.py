import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langsmith import Client as LangSmithClient
from starlette.websockets import WebSocketDisconnect
from wasabi import msg  # type: ignore[import-untyped]

from goldenverba.unified_verba_manager import VerbaManager, ClientManager
from goldenverba.server.helpers import BatchManager, LoggerManager

# Import types
from goldenverba.server.types import (
    ChunksPayload,
    ConnectPayload,
    Credentials,
    DataBatchPayload,
    DatacountPayload,
    DeleteSuggestionPayload,
    FeedbackPayload,
    GeneratePayload,
    GetAllSuggestionsPayload,
    GetChunkPayload,
    GetContentPayload,
    GetDocumentPayload,
    GetSuggestionsPayload,
    GetVectorPayload,
    QueryPayload,
    ResetPayload,
    SearchQueryPayload,
    SetRAGConfigPayload,
    SetThemeConfigPayload,
    SetUserConfigPayload,
)
# Unified PostgreSQL manager imported above

# Set up logging
logger = logging.getLogger(__name__)

load_dotenv()

# Check if runs in production
production_key = os.environ.get("VERBA_PRODUCTION")
tag = os.environ.get("VERBA_GOOGLE_TAG", "")

if production_key:
    msg.info(f"Verba runs in {production_key} mode")
    production = production_key
else:
    production = "Local"

manager = VerbaManager()

# Use unified ClientManager for connection pooling
client_manager = ClientManager()

### Lifespan


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await client_manager.disconnect()


# FastAPI App
app = FastAPI(lifespan=lifespan)

# Allow requests only from the same origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This will be restricted by the custom middleware
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom middleware to check if the request is from the same origin
@app.middleware("http")
async def check_same_origin(
    request: Request, call_next: Callable[[Request], Any]
) -> Response:
    # Allow public access to /api/health
    if request.url.path == "/api/health":
        return await call_next(request)

    origin = request.headers.get("origin")
    allowed_origins = [
        str(request.base_url).rstrip("/"),
        "http://localhost:3000",  # Local development
        "https://hgg-verba-production.up.railway.app",  # Update this to your Railway URL
        "hgg-verba.railway.internal",
        "*.up.railway.app",  # Allow all Railway apps (optional)
    ]

    if origin in allowed_origins:
        return await call_next(request)
    else:
        # Only apply restrictions to /api/ routes (except /api/health)
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Not allowed",
                    "details": {
                        "request_origin": origin,
                        "expected_origin": allowed_origins,
                    },
                },
            )
        return await call_next(request)


BASE_DIR = Path(__file__).resolve().parent

# Serve the assets (JS, CSS, images, etc.)
app.mount(
    "/static/_next",
    StaticFiles(directory=BASE_DIR / "frontend/out/_next"),
    name="next-assets",
)

# Serve the main page and other static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend/out"), name="app")


@app.get("/")
@app.head("/")
async def serve_frontend() -> FileResponse:
    return FileResponse(os.path.join(BASE_DIR, "frontend/out/index.html"))


### INITIAL ENDPOINTS


# Define health check endpoint
@app.get("/api/health")
async def health_check() -> JSONResponse:
    await client_manager.clean_up()

    if production == "Local":
        deployments = await manager.get_deployments()
    else:
        deployments = {"DATABASE_URL": "", "POSTGRES_HOST": "", "POSTGRES_PASSWORD": ""}

    return JSONResponse(
        content={
            "message": "Alive!",
            "production": production,
            "gtag": tag,
            "deployments": deployments,
        }
    )


@app.get("/api/health/websocket")
async def websocket_health() -> JSONResponse:
    """Check WebSocket server health."""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "websocket_endpoints": ["/ws/generate_stream", "/ws/import_files"],
        }
    )


@app.post("/api/connect")
async def connect_to_verba(payload: ConnectPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        config = await manager.load_rag_config(client)
        user_config = await manager.load_user_config(client)
        theme, themes = await manager.load_theme_config(client)
        return JSONResponse(
            status_code=200,
            content={
                "connected": True,
                "error": "",
                "rag_config": config,
                "user_config": user_config,
                "theme": theme,
                "themes": themes,
            },
        )
    except Exception as e:
        msg.fail(f"Failed to connect to PostgreSQL {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "connected": False,
                "error": f"Failed to connect to PostgreSQL {str(e)}",
                "rag_config": {},
                "theme": {},
                "themes": {},
            },
        )


### WEBSOCKETS


@app.websocket("/ws/generate_stream")
async def websocket_generate_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:  # Start a loop to keep the connection alive.
        try:
            data = await websocket.receive_text()

            # First, try to parse as JSON to check message type
            try:
                json_data = json.loads(data)
                # Handle ping messages
                if isinstance(json_data, dict) and json_data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
            except json.JSONDecodeError:
                pass

            # Parse and validate the JSON string using Pydantic model
            payload = GeneratePayload.model_validate_json(data)

            msg.good(f"Received generate stream call for {payload.query}")

            full_text = ""
            reasoning_text = ""
            async for chunk in manager.generate_stream_answer(
                payload.rag_config,
                payload.query,
                payload.context,
                payload.conversation,
            ):
                # Ensure that any UUIDs are converted to strings
                if isinstance(chunk.get("runId"), UUID):
                    chunk["runId"] = str(chunk["runId"])

                # Handle different message types
                if chunk.get("type") == "reasoning" or chunk.get("type") == "thinking":
                    reasoning_text += chunk["message"]
                elif chunk.get("type") != "transition":
                    full_text += chunk["message"]

                if chunk["finish_reason"] == "stop":
                    chunk["full_text"] = full_text
                    if reasoning_text:
                        chunk["reasoning_text"] = reasoning_text
                msg.good(f"Sending chunk: {chunk}")  # Log the chunk being sent
                await websocket.send_json(chunk)

        except WebSocketDisconnect:
            msg.warn("WebSocket connection closed by client.")
            break  # Break out of the loop when the client disconnects

        except Exception as e:
            msg.fail(f"WebSocket Error: {str(e)}")
            await websocket.send_json(
                {"message": str(e), "finish_reason": "stop", "full_text": str(e)}
            )
        msg.good("Successfully streamed answer")


@app.websocket("/ws/import_files")
async def websocket_import_files(websocket: WebSocket) -> None:
    if production == "Demo":
        return

    await websocket.accept()
    logger = LoggerManager(websocket)
    batcher = BatchManager()

    while True:
        try:
            data = await websocket.receive_text()

            # First, try to parse as JSON to check message type
            try:
                json_data = json.loads(data)
                # Handle ping messages
                if isinstance(json_data, dict) and json_data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
            except json.JSONDecodeError:
                pass

            batch_data = DataBatchPayload.model_validate_json(data)
            fileConfig = batcher.add_batch(batch_data)
            if fileConfig is not None:
                client = await client_manager.connect(batch_data.credentials)
                await asyncio.create_task(
                    manager.import_document(client, fileConfig, logger)
                )

        except WebSocketDisconnect:
            msg.warn("Import WebSocket connection closed by client.")
            break
        except Exception as e:
            msg.fail(f"Import WebSocket Error: {str(e)}")
            break


### CONFIG ENDPOINTS


# Get Configuration
@app.post("/api/get_rag_config")
async def retrieve_rag_config(payload: Credentials) -> JSONResponse:
    try:
        client = await client_manager.connect(payload)
        config = await manager.load_rag_config(client)
        return JSONResponse(
            status_code=200, content={"rag_config": config, "error": ""}
        )

    except Exception as e:
        msg.warn(f"Could not retrieve configuration: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "rag_config": {},
                "error": f"Could not retrieve rag configuration: {str(e)}",
            },
        )


@app.post("/api/set_rag_config")
async def update_rag_config(payload: SetRAGConfigPayload) -> JSONResponse:
    if production == "Demo":
        return JSONResponse(
            content={
                "status": "200",
                "status_msg": "Config can't be updated in Production Mode",
            }
        )

    try:
        client = await client_manager.connect(payload.credentials)
        await manager.set_rag_config(client, payload.rag_config.model_dump())
        return JSONResponse(
            content={
                "status": 200,
            }
        )
    except Exception as e:
        msg.warn(f"Failed to set new RAG Config {str(e)}")
        return JSONResponse(
            content={
                "status": 400,
                "status_msg": f"Failed to set new RAG Config {str(e)}",
            }
        )


@app.post("/api/get_user_config")
async def retrieve_user_config(payload: Credentials) -> JSONResponse:
    try:
        client = await client_manager.connect(payload)
        config = await manager.load_user_config(client)
        return JSONResponse(
            status_code=200, content={"user_config": config, "error": ""}
        )

    except Exception as e:
        msg.warn(f"Could not retrieve user configuration: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "user_config": {},
                "error": f"Could not retrieve rag configuration: {str(e)}",
            },
        )


@app.post("/api/set_user_config")
async def update_user_config(payload: SetUserConfigPayload) -> JSONResponse:
    if production == "Demo":
        return JSONResponse(
            content={
                "status": "200",
                "status_msg": "Config can't be updated in Production Mode",
            }
        )

    try:
        client = await client_manager.connect(payload.credentials)
        await manager.set_user_config(client, payload.user_config)
        return JSONResponse(
            content={
                "status": 200,
                "status_msg": "User config updated",
            }
        )
    except Exception as e:
        msg.warn(f"Failed to set new RAG Config {str(e)}")
        return JSONResponse(
            content={
                "status": 400,
                "status_msg": f"Failed to set new RAG Config {str(e)}",
            }
        )


# Get Configuration
@app.post("/api/get_theme_config")
async def retrieve_theme_config(payload: Credentials) -> JSONResponse:
    try:
        client = await client_manager.connect(payload)
        theme, themes = await manager.load_theme_config(client)
        return JSONResponse(
            status_code=200, content={"theme": theme, "themes": themes, "error": ""}
        )

    except Exception as e:
        msg.warn(f"Could not retrieve configuration: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "theme": None,
                "themes": None,
                "error": f"Could not retrieve theme configuration: {str(e)}",
            },
        )


@app.post("/api/set_theme_config")
async def update_theme_config(payload: SetThemeConfigPayload) -> JSONResponse:
    if production == "Demo":
        return JSONResponse(
            content={
                "status": "200",
                "status_msg": "Config can't be updated in Production Mode",
            }
        )

    try:
        client = await client_manager.connect(payload.credentials)
        await manager.set_theme_config(
            client, {"theme": payload.theme, "themes": payload.themes}
        )
        return JSONResponse(
            content={
                "status": 200,
            }
        )
    except Exception as e:
        msg.warn(f"Failed to set new RAG Config {str(e)}")
        return JSONResponse(
            content={
                "status": 400,
                "status_msg": f"Failed to set new RAG Config {str(e)}",
            }
        )


### RAG ENDPOINTS


# Receive query and return chunks and query answer
@app.post("/api/query")
async def query(payload: QueryPayload) -> JSONResponse:
    msg.good(f"Received query: {payload.query}")
    try:
        client = await client_manager.connect(payload.credentials)
        documents_uuid = [document.uuid for document in payload.documentFilter]
        documents, context = await manager.retrieve_chunks(
            client, payload.query, payload.RAG, payload.labels, documents_uuid
        )

        return JSONResponse(
            content={"error": "", "documents": documents, "context": context}
        )
    except Exception as e:
        msg.warn(f"Query failed: {str(e)}")
        return JSONResponse(
            content={"error": f"Query failed: {str(e)}", "documents": [], "context": ""}
        )


### DOCUMENT ENDPOINTS


# Retrieve specific document based on UUID
@app.post("/api/get_document")
async def get_document(payload: GetDocumentPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        document = await manager.database_manager.get_document(
            payload.uuid,
            properties=[
                "title",
                "extension",
                "fileSize",
                "labels",
                "source",
                "meta",
                "metadata",
            ],
        )
        if document is not None:
            document["content"] = ""
            msg.good(f"Succesfully retrieved document: {document['title']}")
            return JSONResponse(
                content={
                    "error": "",
                    "document": document,
                }
            )
        else:
            msg.warn("Could't retrieve document")
            return JSONResponse(
                content={
                    "error": "Couldn't retrieve requested document",
                    "document": None,
                }
            )
    except Exception as e:
        msg.fail(f"Document retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "error": str(e),
                "document": None,
            }
        )


@app.post("/api/get_datacount")
async def get_document_count(payload: DatacountPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        document_uuids = [document.uuid for document in payload.documentFilter]
        datacount = await manager.database_manager.get_datacount(
            payload.embedding_model, document_uuids
        )
        return JSONResponse(
            content={
                "datacount": datacount,
            }
        )
    except Exception as e:
        msg.fail(f"Document Count retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "datacount": 0,
            }
        )


@app.post("/api/get_labels")
async def get_labels(payload: Credentials) -> JSONResponse:
    try:
        client = await client_manager.connect(payload)
        labels = await manager.database_manager.get_labels()
        return JSONResponse(
            content={
                "labels": labels,
            }
        )
    except Exception as e:
        msg.fail(f"Document Labels retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "labels": [],
            }
        )


# Retrieve specific document based on UUID
@app.post("/api/get_content")
async def get_content(payload: GetContentPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        content, maxPage = await manager.get_content(
            client, payload.uuid, payload.page - 1, payload.chunkScores
        )
        msg.good(f"Succesfully retrieved content from {payload.uuid}")
        return JSONResponse(
            content={"error": "", "content": content, "maxPage": maxPage}
        )
    except Exception as e:
        msg.fail(f"Document retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "error": str(e),
                "document": None,
            }
        )


# Retrieve specific document based on UUID
@app.post("/api/get_vectors")
async def get_vectors(payload: GetVectorPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        vector_groups = await manager.database_manager.get_vectors(
            payload.uuid, payload.showAll
        )
        return JSONResponse(
            content={
                "error": "",
                "vector_groups": vector_groups,
            }
        )
    except Exception as e:
        msg.fail(f"Vector retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "error": str(e),
                "payload": {"embedder": "None", "vectors": []},
            }
        )


# Retrieve specific document based on UUID
@app.post("/api/get_chunks")
async def get_chunks(payload: ChunksPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        chunks = await manager.database_manager.get_chunks(
            payload.uuid, payload.page, payload.pageSize
        )
        return JSONResponse(
            content={
                "error": "",
                "chunks": chunks,
            }
        )
    except Exception as e:
        msg.fail(f"Chunk retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "error": str(e),
                "chunks": None,
            }
        )


# Retrieve specific document based on UUID
@app.post("/api/get_chunk")
async def get_chunk(payload: GetChunkPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        chunk = await manager.database_manager.get_chunk(
            payload.uuid, payload.embedder
        )
        return JSONResponse(
            content={
                "error": "",
                "chunk": chunk,
            }
        )
    except Exception as e:
        msg.fail(f"Chunk retrieval failed: {str(e)}")
        return JSONResponse(
            content={
                "error": str(e),
                "chunk": None,
            }
        )


## Retrieve and search documents imported to PostgreSQL
@app.post("/api/get_all_documents")
async def get_all_documents(payload: SearchQueryPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        documents, total_count = await manager.database_manager.get_documents(
            payload.query,
            payload.pageSize,
            payload.page,
            payload.labels,
            properties=["title", "extension", "fileSize", "labels", "source", "meta"],
        )
        labels = await manager.database_manager.get_labels()

        msg.good(f"Succesfully retrieved document: {len(documents)} documents")
        return JSONResponse(
            content={
                "documents": documents,
                "labels": labels,
                "error": "",
                "totalDocuments": total_count,
            }
        )
    except Exception as e:
        msg.fail(f"Retrieving all documents failed: {str(e)}")
        return JSONResponse(
            content={
                "documents": [],
                "label": [],
                "error": f"All Document retrieval failed: {str(e)}",
                "totalDocuments": 0,
            }
        )


# Delete specific document based on UUID
@app.post("/api/delete_document")
async def delete_document(payload: GetDocumentPayload) -> JSONResponse:
    if production == "Demo":
        msg.warn("Can't delete documents when in Production Mode")
        return JSONResponse(status_code=200, content={})

    try:
        client = await client_manager.connect(payload.credentials)
        msg.info(f"Deleting {payload.uuid}")
        await manager.database_manager.delete_document(payload.uuid)
        return JSONResponse(status_code=200, content={})

    except Exception as e:
        msg.fail(f"Deleting Document with ID {payload.uuid} failed: {str(e)}")
        return JSONResponse(status_code=400, content={})


### ADMIN


@app.post("/api/reset")
async def reset_verba(payload: ResetPayload) -> JSONResponse:
    if production == "Demo":
        return JSONResponse(status_code=200, content={})

    try:
        client = await client_manager.connect(payload.credentials)
        if payload.resetMode == "ALL":
            await manager.database_manager.delete_all()
        elif payload.resetMode == "DOCUMENTS":
            await manager.database_manager.delete_all_documents()
        elif payload.resetMode == "CONFIG":
            await manager.database_manager.delete_all_configs()
        elif payload.resetMode == "SUGGESTIONS":
            await manager.database_manager.delete_all_suggestions()

        msg.info(f"Resetting Verba in ({payload.resetMode}) mode")

        return JSONResponse(status_code=200, content={})

    except Exception as e:
        msg.warn(f"Failed to reset Verba {str(e)}")
        return JSONResponse(status_code=500, content={})


# Get Status meta data
@app.post("/api/get_meta")
async def get_meta(payload: Credentials) -> JSONResponse:
    try:
        client = await client_manager.connect(payload)
        node_payload, collection_payload = await manager.database_manager.get_metadata()
        return JSONResponse(
            content={
                "error": "",
                "node_payload": node_payload,
                "collection_payload": collection_payload,
            }
        )
    except Exception as e:
        return JSONResponse(
            content={
                "error": f"Couldn't retrieve metadata {str(e)}",
                "node_payload": {},
                "collection_payload": {},
            }
        )


### Suggestions


@app.post("/api/get_suggestions")
async def get_suggestions(payload: GetSuggestionsPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        suggestions = await manager.database_manager.retrieve_suggestions(
            payload.query, payload.limit
        )
        return JSONResponse(
            content={
                "suggestions": suggestions,
            }
        )
    except Exception:
        return JSONResponse(
            content={
                "suggestions": [],
            }
        )


@app.post("/api/get_all_suggestions")
async def get_all_suggestions(payload: GetAllSuggestionsPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        (
            suggestions,
            total_count,
        ) = await manager.database_manager.retrieve_all_suggestions(
            payload.page, payload.pageSize
        )
        return JSONResponse(
            content={
                "suggestions": suggestions,
                "total_count": total_count,
            }
        )
    except Exception:
        return JSONResponse(
            content={
                "suggestions": [],
                "total_count": 0,
            }
        )


@app.post("/api/delete_suggestion")
async def delete_suggestion(payload: DeleteSuggestionPayload) -> JSONResponse:
    try:
        client = await client_manager.connect(payload.credentials)
        await manager.database_manager.delete_suggestions(payload.uuid)
        return JSONResponse(
            content={
                "status": 200,
            }
        )
    except Exception:
        return JSONResponse(
            content={
                "status": 400,
            }
        )


@app.post("/api/feedback")
async def submit_feedback(payload: FeedbackPayload) -> JSONResponse:
    logger.info(
        f"Received feedback request: runId={payload.runId}, feedbackType={payload.feedbackType}"
    )
    try:
        client = LangSmithClient(
            api_url=payload.credentials["url"]
            if "url" in payload.credentials
            else None,
            api_key=payload.credentials["key"]
            if "key" in payload.credentials
            else None,
        )

        feedback_score = 1 if payload.feedbackType == "positive" else 0

        feedback = client.create_feedback(
            run_id=payload.runId,
            key="user_rating",
            score=feedback_score,
            comment=payload.additionalFeedback,
            value=payload.feedbackType,
        )

        logger.info(f"Feedback submitted successfully: feedback_id={feedback.id}")
        return {"status": "success", "feedback_id": str(feedback.id)}
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return {"status": "error", "message": str(e)}
