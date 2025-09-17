from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import json
import os
from .file_service import process_pdf_file, process_text_file, store_file_chunks
from .schemas import ChatRequest, ChatResponse, FileUploadResponse, Conversation, Message
from .llm_service import generate_embedding, generate_response, generate_response_stream
from .vector_db import query_embeddings
from .rag import build_context
from .conversation_service import (
    create_conversation, get_conversation, get_conversations, 
    add_message, get_conversation_messages, get_last_assistant_response_id
)
from .guardrails import guardrails

load_dotenv()

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://chatbot-olive-eight-14.vercel.app/")
app = FastAPI(title="Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a text or PDF file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ["txt", "pdf"]:
            raise HTTPException(status_code=400, detail="Only .txt and .pdf files are supported")
        
        content = await file.read()

        if file_extension == "txt":
            text_content = content.decode("utf-8")
            items = process_text_file(text_content, file.filename)
        elif file_extension == "pdf":
            items = process_pdf_file(content, file.filename)

        chunks_added = store_file_chunks(items)

        return FileUploadResponse(
            message=f"{file.filename} processed successfully",
            file_id=file.filename,
            chunks_added=chunks_added
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Non-streaming chat endpoint with conversation threading"""
    try:
        is_input_safe, input_msg, _ = guardrails.check_input_safety(req.query)
        if not is_input_safe:
            def error_generate():
                yield f"data : {{\"error\": \"Input blocked by guardrails: {input_msg}\"}}\n\n"
            return StreamingResponse(error_generate(), media_type="text/plain")
            
        # Generate embedding for user query
        q_emb = generate_embedding(req.query)

        # Query vector database for relevant context
        matches = query_embeddings(q_emb, top_k=req.top_k, filter=None)
        context = build_context(matches)

        # Get previous response ID for conversation threading
        previous_response_id = None
        if req.conversation_id:
            previous_response_id = get_last_assistant_response_id(req.conversation_id)

        # Generate response with conversation threading
        answer, response_id = generate_response(req.query, context, previous_response_id)

        # Create or get conversation
        if req.conversation_id:
            conversation = get_conversation(req.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation with first few words of query as title
            title = req.query[:50] + "..." if len(req.query) > 50 else req.query
            conversation = create_conversation(title)

        # Add user message
        user_message = add_message(conversation.id, "user", req.query)
        
        # Output Guardrails
        final_content = answer
        is_output_safe, out_msg, _ = guardrails.check_output_safety(final_content)
        if not is_output_safe:
            final_content = guardrails.get_safe_response(final_content)
        
        # Add assistant message with response_id for threading
        assistant_message = add_message(
            conversation.id, 
            "assistant", 
            final_content, 
            response_id=response_id,
            parent_message_id=user_message.id
        )

        return ChatResponse(
            answer=final_content,
            message_id=assistant_message.id,
            conversation_id=conversation.id,
            response_id=response_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """Streaming chat endpoint with conversation threading"""
    try:
        is_input_safe, input_msg, _ = guardrails.check_input_safety(req.query)
        if not is_input_safe:
            def error_generate():
                yield f"data : {{\"error\": \"Input blocked by guardrails: {input_msg}\"}}\n\n"
            return StreamingResponse(error_generate(), media_type="text/plain")
        # Generate embedding for user query
        q_emb = generate_embedding(req.query)

        # Query vector database for relevant context
        matches = query_embeddings(q_emb, top_k=req.top_k, filter=None)
        context = build_context(matches)

        # Get previous response ID for conversation threading AND build limited history
        previous_response_id = None
        history_text = ""
        if req.conversation_id:
            previous_response_id = get_last_assistant_response_id(req.conversation_id)
            past = get_conversation_messages(req.conversation_id)
            recent = past[-5:] if len(past) > 5 else past
            history_text = "\n".join(
                [("User: " if m.role == "user" else "Assistant: ") + m.content for m in recent]
            )

        def generate(
            history_text=history_text,
            previous_response_id=previous_response_id,
            context=context
        ):
            # Create or get conversation
            if req.conversation_id:
                conversation = get_conversation(req.conversation_id)
                if not conversation:
                    # Auto create a new conversation if the provided ID is missing
                    title = req.query[:50] + "..." if len(req.query) > 50 else req.query
                    conversation = create_conversation(title)
            else:
                # Create new conversation
                title = req.query[:50] + "..." if len(req.query) > 50 else req.query
                conversation = create_conversation(title)

            # Add user message
            user_message = add_message(conversation.id, "user", req.query)
            
            # Send conversation info
            yield f"data: {json.dumps({'conversation_id': conversation.id, 'user_message_id': user_message.id})}\n\n"

            # Stream response with conversation threading
            full_response = ""
            response_id = None
            
            try:
                for event in generate_response_stream(
                    req.query, context, previous_response_id, history=history_text
                ):
                    if event["type"] == "metadata":
                        response_id = event["response_id"]
                    elif event["type"] == "content":
                        content = event["content"]
                        if content:  # Only yield non-empty content
                            full_response += content
                            yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                    elif event["type"] == "done":
                        # Use the full_content if available, otherwise use accumulated content
                        final_content = event.get("full_content", full_response)
                        response_id = event.get("response_id", response_id)
                        
                        # Output Guardrails
                        is_output_safe, out_msg, _ = guardrails.check_output_safety(final_content)
                        if not is_output_safe:
                            final_content = guardrails.get_safe_response(final_content)

                        # Add assistant message to database with response_id
                        assistant_message = add_message(
                            conversation.id, 
                            "assistant", 
                            final_content, 
                            response_id=response_id,
                            parent_message_id=user_message.id
                        )
                        
                        # Send completion signal
                        yield f"data: {json.dumps({'content': '', 'done': True, 'message_id': assistant_message.id, 'response_id': response_id})}\n\n"
            except Exception as e:
                print(f"Error in streaming loop: {e}")
                # Fallback: send error message
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise ValueError("Error in chat stream - ", str(e))

@app.get("/conversations", response_model=list[Conversation])
def get_conversations_endpoint():
    """Get all conversations"""
    return get_conversations()

@app.get("/conversations/{conversation_id}/messages", response_model=list[Message])
def get_conversation_messages_endpoint(conversation_id: str):
    """Get messages for a conversation"""
    return get_conversation_messages(conversation_id)

        