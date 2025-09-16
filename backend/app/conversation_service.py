import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from .schemas import Conversation, Message

# Simple file-based storage (you can replace with a database later)
CONVERSATIONS_FILE = "conversations.json"
MESSAGES_FILE = "messages.json"

def load_conversations() -> Dict[str, Conversation]:
    """Load conversations from file"""
    if os.path.exists(CONVERSATIONS_FILE):
        try:
            if os.path.getsize(CONVERSATIONS_FILE) == 0:
                return {}
            with open(CONVERSATIONS_FILE, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return {}
                return {k: Conversation(**v) for k, v in data.items()}
        except (json.JSONDecodeError, ValueError, TypeError):
            # Corrupt or invalid JSON; treat as empty store
            return {}
    return {}

def save_conversations(conversations: Dict[str, Conversation]):
    """Save conversations to file"""
    data = {k: v.model_dump() for k, v in conversations.items()}  # Fixed: use .dict() not .model_dump()
    with open(CONVERSATIONS_FILE, 'w') as f:
        json.dump(data, f, default=str)

def load_messages() -> List[Message]:
    """Load messages from file"""
    if os.path.exists(MESSAGES_FILE):
        try:
            if os.path.getsize(MESSAGES_FILE) == 0:
                return []
            with open(MESSAGES_FILE, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return [Message(**msg) for msg in data]
        except (json.JSONDecodeError, ValueError, TypeError):
            # Corrupt or invalid JSON; treat as empty list
            return []
    return []

def save_messages(messages: List[Message]):
    """Save messages to file"""
    data = [msg.model_dump() for msg in messages]  # Fixed: use .dict() not .model_dump()
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(data, f, default=str)

def create_conversation(title: str) -> Conversation:
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    now = datetime.now()
    
    conversation = Conversation(
        id=conversation_id,
        title=title,
        created_at=now,
        updated_at=now
    )
    
    conversations = load_conversations()
    conversations[conversation_id] = conversation
    save_conversations(conversations)
    
    return conversation

def get_conversation(conversation_id: str) -> Optional[Conversation]:
    """Get a conversation by ID"""
    conversations = load_conversations()
    return conversations.get(conversation_id)

def get_conversations() -> List[Conversation]:
    """Get all conversations"""
    conversations = load_conversations()
    return sorted(conversations.values(), key=lambda x: x.updated_at, reverse=True)

def add_message(
    conversation_id: str,
    role: str,
    content: str,
    response_id: Optional[str] = None,
    parent_message_id: Optional[str] = None
) -> Message:
    """Add a message to a conversation"""
    message_id = str(uuid.uuid4())
    now = datetime.now()
    
    message = Message(
        id=message_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        response_id=response_id,
        parent_message_id=parent_message_id,
        created_at=now
    )
    
    messages = load_messages()
    messages.append(message)
    save_messages(messages)
    
    # Update conversation timestamp
    conversations = load_conversations()
    if conversation_id in conversations:
        conversations[conversation_id].updated_at = now
        save_conversations(conversations)
    
    return message

def get_conversation_messages(conversation_id: str) -> List[Message]:
    """Get all messages for a conversation"""
    messages = load_messages()
    return [msg for msg in messages if msg.conversation_id == conversation_id]

def get_last_assistant_response_id(conversation_id: str) -> Optional[str]:
    """Get the response_id of the last assistant message for conversation threading"""
    messages = get_conversation_messages(conversation_id)
    
    # Find the last assistant message with a response_id
    for message in reversed(messages):
        if message.role == "assistant" and message.response_id:
            return message.response_id
    
    return None

