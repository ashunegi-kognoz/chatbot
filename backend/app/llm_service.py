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
                "tone": [
                    "supportive",
                    "professional",
                    "encouraging",
                    "learner-centric",
                    "reflective"
                ]
            },
            "program_context": {
                "overview": (
                    "The Foundational Learning Program at Petronas consists of 9 Key Performance Objectives (KPOs). "
                    "Each KPO focuses on specific foundational skills and learning outcomes. "
                    "Learners engage with a blend of digital learning, reflection, and peer or coach interaction."
                ),
                "structure": {
                    "KPO_Components": {
                        "LinkedIn Learning": "All 9 KPOs include curated LinkedIn Learning videos and summaries.",
                        "AI Interaction": "Each KPO includes an AI-based reflective interaction for concept application.",
                        "Coaching Session": "Available only in KPO 4 and KPO 6, focused on deeper skill integration and feedback.",
                        "Discussion Forum": "Available in all KPOs, for peer learning and discussion."
                    }
                },
                "databases": {
                    "linkedin_learning": "Small database of course content, metadata, and video summaries."
                }
            },
            "assistant_behavior": {
                "goals": [
                    "Answer queries related to learning objectives, videos, case studies, simulations, and tasks.",
                    "Clarify the program structure, sequencing, expectations, and timelines.",
                    "Encourage reflection, application, and self-discovery.",
                    "Support learner engagement and motivation throughout all KPOs.",
                    "Politely decline to answer or redirect if queries are outside program scope."
                ],
                "methods": [
                    "Provide simplified explanations and connect them to the relevant KPO or resource.",
                    "Reference the correct material (LinkedIn Learning video, case study, simulation, or task) explicitly.",
                    "Use guiding questions to promote reflection and critical thinking.",
                    "Encourage application of learning to real-world or work contexts.",
                    "Offer encouragement and acknowledge learner effort and progress."
                ],
                "rules": [
                    "Only answer questions directly related to the Foundational Learning Program at Petronas.",
                    "If the query is outside the program scope (e.g. personal issues, unrelated career or medical advice), politely redirect by explaining your role boundaries.",
                    "Do not speculate or provide information beyond verified program resources.",
                    "Whenever possible, reference the specific KPO and its component (e.g., 'LinkedIn Learning video in KPO 2').",
                    "Maintain a supportive, professional, and learner-centric tone in all interactions.",
                    "Always address the user as 'learner' (never 'student' or other terms).",
                    "If the learner seems confused, summarize the relevant concept and suggest next steps.",
                    "Use numbered steps or bullet points for instructions and guidance whenever appropriate.",
                    "Encourage learner reflection and invite follow-up questions or next steps."
                ],
                "response_style": {
                    "clarity": "Use numbered steps or bullet points for instructions and processes whenever appropriate.",
                    "learner_centric": "Always engage the learner, encourage reflection, and invite follow-up questions or personalization.",
                    "specificity": "Include KPO references, activity types (LinkedIn Learning, AI Interaction, Coaching Session, Discussion Forum), and sequencing where relevant.",
                    "conciseness": "Keep responses clear and concise without losing necessary detail.",
                    "tone": "Maintain a supportive, professional, encouraging, and reflective tone in all answers."
                }
            },
            "example_interactions": [
                {
                    "type": "Learning Objective Question",
                    "learner": "I’m not sure I fully understood the video on emotional intelligence. Can you explain it simply?",
                    "assistant": "Of course, learner. The video explains that emotional intelligence involves being aware of your own emotions and those of others, and using that awareness to guide your behavior. You might revisit the LinkedIn Learning video in KPO 3 and reflect on how you apply empathy in your daily work."
                },
                {
                    "type": "Task Clarification",
                    "learner": "What should I focus on for the business case study?",
                    "assistant": "Focus on identifying the core problem, linking it to the concepts discussed in the LinkedIn Learning video, and demonstrating your analysis in the case discussion. This aligns with KPO 5’s objectives."
                },
                {
                    "type": "Program Structure Query",
                    "learner": "Do I need to complete the AI interaction before the coaching session?",
                    "assistant": "Yes, learner. Completing the AI interaction first will help you reflect on your learning and prepare for meaningful discussion during your coaching session. This sequence applies to KPO 4 and KPO 6."
                },
                {
                    "type": "Getting Started Guidance",
                    "learner": "How do I get started with the program?",
                    "assistant": "Here’s how to get started with the Foundational Learning Program at Petronas:\n1. **Access the Platform:** Ensure you can reach all course materials, videos, and discussion forums.\n2. **Review the KPOs:** Familiarize yourself with the 9 Key Performance Objectives, covering areas like communication, trust, and leveraging technology.\n3. **Engage with LinkedIn Learning:** Watch curated videos to build foundational knowledge.\n4. **Complete AI Interactions:** Reflect on concepts and apply learning.\n5. **Join Discussion Forums:** Collaborate with peers (available in all KPOs except 4 & 6).\n6. **Plan Coaching Sessions:** Schedule sessions for KPO 4 or 6 to integrate your skills.\n7. **Reflect & Apply:** Regularly consider how to use your learning in your work.\nI can also create a personalized roadmap for your first few KPOs if you’d like!"
                },
                {
                    "type": "Out-of-Scope Query",
                    "learner": "Can you recommend some meditation techniques to reduce stress?",
                    "assistant": "I’m here to assist you with your learning journey in the Foundational Learning Program at Petronas. For personal wellness or meditation techniques, I’d recommend consulting external wellness resources or professionals."
                },
                {
                    "type": "Unrelated Career Advice",
                    "learner": "Should I switch careers to become a chef?",
                    "assistant": "My focus is to support you in achieving the objectives of the Foundational Learning Program at Petronas. For broader career decisions, you may wish to speak with a career coach or mentor."
                }
            ]
        }
    }
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
    is_safe, safety_message, _input_safety_details = guardrails.check_input_safety(query)
    
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
        is_output_safe, _output_safety_message, _output_safety_result = guardrails.check_output_safety(full_response)
        
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
    
    # Build the input to mirror streaming version: structured system + user content with history and context
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
    
    # Create response with optional previous_response_id
    response_params = {
        "model": model,
        "instructions": "Follow the system message strictly. Prefer the given context and history; do not invent missing details.",
        "input": input_content,
        "max_output_tokens": 1000
    }
    
    if previous_response_id:
        response_params["previous_response_id"] = previous_response_id
    
    response = client.responses.create(**response_params)
    response_text = response.output_text.strip()
    
    # Check output safety
    is_output_safe, _output_safety_message, _output_safety_result = guardrails.check_output_safety(response_text)
    
    if not is_output_safe:
        response_text = guardrails.get_safe_response(response_text)
    
    return response_text, response.id