import os
from typing import Generator, Optional
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_foundational_system_prompt() -> str:
    """Return the structured system prompt for the Foundational Learning Coach."""
    system_payload = {
        "role": "system",
        "name": "FoundationalLearningCoach",
        "content": {
            "persona": {
                "role": "AI Assistant acting as a supportive coach",
                "program": "Foundational Learning Program at Petronas",
                "tone": ["supportive", "professional", "encouraging", "learner-centric"]
            },
            "program_context": {
                "format": [
                    "Curated LinkedIn Learning videos",
                    "AI conversational assessment",
                    "Business Case Study",
                    "Simulation or Coaching Session",
                    "Optional Discussion Forum"
                ],
                "databases": {
                    "linkedin_learning": "small database of course content & summaries"
                }
            },
            "assistant_behavior": {
                "goals": [
                    "Answer queries related to learning objectives, videos, case studies, simulations, and tasks",
                    "Clarify program structure, expectations, and deadlines",
                    "Encourage reflection, application, and self-discovery",
                    "Redirect politely if queries are outside program scope"
                ],
                "methods": [
                    "Provide simplified explanations when needed",
                    "Reference the correct resource (video, case study, simulation, or task)",
                    "Encourage critical thinking and problem-solving",
                    "Offer guiding questions, examples, and analogies"
                ],
                "rules": [
                    "Only answer questions that are directly related to the Foundational Learning Program at Petronas.",
                    "If the query is outside the scope (e.g. unrelated personal advice, medical questions, unrelated career advice), politely redirect the learner by saying that you can only assist within the program scope.",
                    "Never attempt to answer or guess beyond available resources or knowledge.",
                    "Always reference the correct resource when answering, or explain why it’s unavailable.",
                    "Maintain the supportive, professional, and learner-centric tone in all interactions."
            ],
            },
            "example_interactions": [
                {
                    "type": "Learning Objective Question",
                    "learner": "I’m not sure I fully understood the video on emotional intelligence. Can you explain it simply?",
                    "assistant": "Provide a simplified explanation, reference the LinkedIn Learning video, and suggest a reflection exercise."
                },
                {
                    "type": "Task Clarification",
                    "learner": "What should I focus on for the business case study?",
                    "assistant": "Outline case study requirements, link key learning objectives, and encourage use of concepts from videos."
                },
                {
                    "type": "Program Structure Query",
                    "learner": "Do I need to complete the simulation before the coaching session?",
                    "assistant": "Clarify sequencing, explain how activities complement each other, and encourage preparation."
                },
                {
                    "type": "Out-of-Scope Query",
                    "learner": "Can you recommend some meditation techniques to reduce stress?",
                    "assistant": "I'm here to assist you with the Foundational Learning Program at Petronas. For meditation techniques, you might want to explore other resources or speak with a wellness professional."
                },
                {
                    "type": "Unrelated Career Advice",
                    "learner": "Should I switch careers to become a chef?",
                    "assistant": "My expertise is focused on helping you achieve learning objectives within the Foundational Learning Program at Petronas. For career guidance, you might want to consult a career coach."
                }
            ]
        }
    }
    # We pass this structured payload as a JSON string so the model can parse and follow it.
    return json.dumps(system_payload, ensure_ascii=False)


def generate_embedding(text, model = "text-embedding-3-large"):
    text = text.replace("\n", " ")
    response = client.embeddings.create(
        input=text,
        model=model
    )

    return response.data[0].embedding


def generate_response_stream(
    query: str, 
    context: str, 
    previous_response_id: Optional[str] = None,
    model: str = "gpt-4o",
    history: str = ""
) -> Generator[dict, None, None]:
    """Generate streaming response using Responses API with conversation threading and guardrails"""
    
    # Import guardrails here to avoid circular imports
    from .guardrails import guardrails
    
    # Check input safety first
    is_safe, safety_message, safety_result = guardrails.check_input_safety(query)
    
    if not is_safe:
        yield {"type": "content", "content": safety_message}
        yield {"type": "done", "response_id": None}
        return
    
    # Build the input with context and structured system message
    system_message = {
        "role": "system",
        "content": build_foundational_system_prompt()
    }
    
    input_content = [
        system_message,
        {
            "role": "user",
            "content": (
                f"Conversation history (most recent last):\n{history}\n\n"
                f"Context:\n{context}\n\n"
                f"Query:\n{query}\n\n"
                f"Answer:"
            )
        }
    ]
    
    # Create streaming response with optional previous_response_id
    stream_params = {
        "model": model,
        "instructions": "Follow the system message strictly. Prefer the given context and history; do not invent missing details.",
        "input": input_content,
        "max_output_tokens": 1000,
        "stream": True
    }
    
    if previous_response_id:
        stream_params["previous_response_id"] = previous_response_id
    
    try:
        stream = client.responses.create(**stream_params)
        
        # Initialize response_id and collect content
        response_id = None
        full_response = ""
        
        for event in stream:
            # Check for response ID in completed event
            if hasattr(event, 'response') and hasattr(event.response, 'id'):
                response_id = event.response.id
            
            # Check for content delta
            if hasattr(event, 'delta') and event.delta:
                full_response += event.delta
                yield {"type": "content", "content": event.delta}
        
        # Check output safety after streaming is complete
        is_output_safe, output_safety_message, output_safety_result = guardrails.check_output_safety(full_response)
        
        if not is_output_safe:
            # Replace the response with a safe one
            safe_response = guardrails.get_safe_response(full_response)
            yield {"type": "content", "content": f"\n\n{safe_response}"}
        
        # Yield completion signal
        yield {"type": "done", "response_id": response_id}
        
    except Exception as e:
        print(f"Error in streaming: {e}")
        # Fallback to non-streaming
        answer, resp_id = generate_response(query, context, previous_response_id, model, history=history)
        yield {"type": "content", "content": answer}
        yield {"type": "done", "response_id": resp_id}

def generate_response(
    query: str, 
    context: str, 
    previous_response_id: Optional[str] = None,
    model: str = "gpt-4o",
    history: str = ""
) -> tuple[str, str]:
    """Generate non-streaming response using Responses API with conversation threading and guardrails"""
    
    # Import guardrails here to avoid circular imports
    from .guardrails import guardrails
    
    # Check input safety first
    is_safe, safety_message, safety_result = guardrails.check_input_safety(query)
    
    if not is_safe:
        return safety_message, ""
    
    # Build the input with context
    instructions = f"""You are an expert assistant helping students with tasks.
    Use only the provided context, don't give answer outside of that. 
    If the query is irrelevant or inappropriate, politely refuse.
    
    Context from documents:
    {context}"""
    
    input_content = [
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuery:\n{query}\n\nAnswer:"
        }
    ]
    
    # Create response with optional previous_response_id
    response_params = {
        "model": model,
        "instructions": instructions,
        "input": input_content,
        "max_output_tokens": 1000
    }
    
    if previous_response_id:
        response_params["previous_response_id"] = previous_response_id
    
    response = client.responses.create(**response_params)
    response_text = response.output_text.strip()
    
    # Check output safety
    is_output_safe, output_safety_message, output_safety_result = guardrails.check_output_safety(response_text)
    
    if not is_output_safe:
        response_text = guardrails.get_safe_response(response_text)
    
    return response_text, response.id