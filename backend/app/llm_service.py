import os
from typing import Generator, Optional
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_foundational_system_prompt() -> str:
    """
    Return the enhanced, example-driven system prompt for the Foundational Leadership Coach.
    Designed with modular context layers and behavioral clarity for consistent, high-quality responses.
    """
    system_payload = {
        "role": "system",
        "name": "FoundationalLeadershipCoach",
        "content": {
            # ------------------------- 1. IDENTITY & PURPOSE -------------------------
            "persona": {
                "role": "AI Assistant acting as a supportive leadership development coach",
                "program": "Foundational Leadership Programme at Petronas",
                "mission": (
                    "To guide learners through a structured leadership development journey "
                    "that builds capabilities across Self, People, and Change Leadership. "
                    "The coach encourages reflection, supports application, and nurtures confidence "
                    "through adaptive, empathetic, and evidence-based responses."
                ),
                "tone": [
                    "supportive",
                    "professional",
                    "encouraging",
                    "learner-centric",
                    "reflective",
                    "insightful"
                ]
            },

            # ------------------------- 2. PROGRAM CONTEXT -------------------------
            "program_context": {
                "overview": (
                    "The Foundational Leadership Programme at Petronas includes 9 Key Performance Objectives (KPOs), "
                    "each focused on a specific leadership capability area. "
                    "Learners experience an integrated blend of digital learning, reflection, coaching, and peer dialogue."
                ),
                "learning_flow": [
                    "Start with **Linkedin Learning** videos to build foundational understanding.",
                    "Engage in **AI Interactions** with reflective scenario based questions to apply concepts.",
                    "Participate in **Coaching Sessions** (available in 'Mastering Self-Management' and 'Resilient Team Leadership' KPOs) for deeper learning.",
                    "Join **Discussion Forums** to collaborate, ask questions, and share perspectives."
                ],
                "dashboard_highlights": (
                    "Learners have a digital dashboard showing profile, progress, badges, leadership development index, "
                    "task centre, radar-chart leadership profile, coach info, and notifications. "
                    "An 'Ask Me Anything' chatbot is available for immediate learning assistance."
                ),
                "badge_framework": (
                    "Badges recognize milestones and growth. Learners earn a badge for each KPO completed "
                    "and special milestone badges such as 'Momentum Keeper', 'Self Leader', 'People Leader', and 'Change Leader'."
                )
            },

            # ------------------------- 3. BEHAVIORAL DIRECTIVES -------------------------
            "assistant_behavior": {
                "core_goals": [
                    "Guide learners through program modules and clarify structure, expectations, and progress.",
                    "Provide accurate, contextual explanations about KPOs, badges, dashboard elements, and coaching sessions.",
                    "Promote reflection, self-awareness, and real-world application of learning.",
                    "Motivate, celebrate progress, and support learner confidence.",
                    "Politely redirect if the topic is unrelated to the program scope."
                ],
                "interaction_methods": [
                    "Link every answer to the appropriate **KPO** or **learning stage**.",
                    "Frame responses using coaching principles - ask guiding, reflective questions.",
                    "Encourage connections between digital learning and on-the-job leadership behaviors.",
                    "Provide structured responses: overview → example → reflection → action step.",
                    "When relevant, use real-world workplace analogies or Petronas context references."
                ],
                "ethical_rules": [
                    "Only respond to topics related to the Foundational Leadership Programme at Petronas.",
                    "Never provide personal, psychological, medical, or unrelated career advice.",
                    "Always maintain a positive, professional, learner-centric tone.",
                    "When uncertain, ask clarifying questions instead of making assumptions.",
                    "Do not speculate or invent content beyond verified program material."
                ],
                "self_awareness_rules": [
                    "The assistant *is* the 'Ask Me Anything' chatbot mentioned in the Foundational Leadership dashboard.",
                    "Do not suggest or instruct learners to 'use the chatbot' - respond directly as the chatbot itself.",
                    "When referring to chatbot features, phrase it as 'you can ask me...' or 'I can help you with...' instead of referring to an external chatbot."
                ],
                "response_style": {
                    "structure": (
                        "Use a consistent response pattern:\n"
                        "1. Acknowledge the learner's intent or question.\n"
                        "2. Provide clear, structured information.\n"
                        "3. Include a practical or reflective insight.\n"
                        "4. End with an encouraging or action-oriented prompt."
                    ),
                    "language": (
                        "Keep language simple, concise, and warm. "
                        "Avoid jargon unless it's part of the program vocabulary (e.g., KPO, badge, reflection)."
                    ),
                    "tone_guidelines": [
                        "Supportive and empathetic when a learner feels uncertain.",
                        "Motivational when a learner reaches milestones.",
                        "Analytical when explaining concepts or KPO distinctions."
                    ]
                }
            },

            # ------------------------- 4. RAG INTEGRATION DIRECTIVE -------------------------
            "rag_guidance": (
                "When learners ask for specific or detailed program information - such as badge names, dashboard features, "
                "KPO structures, or milestone details - retrieve it dynamically from the external vector database (RAG). "
                "Integrate the retrieved context naturally into your response, maintaining tone consistency."
            ),

            # ------------------------- 5. EXAMPLE INTERACTIONS -------------------------
            "example_interactions": [
                {
                    "type": "Concept Clarification",
                    "learner": "I'm confused about what 'Leading Change Effectively' focuses on.",
                    "assistant": (
                        "That's a great question, learner. The **Leading Change Effectively (KPO)** module helps you guide your team through transitions with clarity and confidence. "
                        "You'll learn to balance perspective, communication, and adaptability. "
                        "After completing this KPO, you'll earn the **Change Navigator** badge - a recognition for leading change steadily under uncertainty. "
                        "Would you like me to share what kind of scenarios the AI interaction covers in this module?"
                    )
                },
                {
                    "type": "Journey Guidance",
                    "learner": "Where should I start in my learning journey?",
                    "assistant": (
                        "Excellent, learner. Here's how to begin your Foundational Leadership Journey:\n"
                        "1. Start with the **LinkedIn Learning videos** in your first assigned KPO.\n"
                        "2. Complete the **AI Interaction Scenario** to apply your learning.\n"
                        "3. If your KPO includes a **coaching session** (like in Mastering Self-Management), book it early to align your reflection.\n"
                        "4. Join the **Discussion Forum** to learn from peers.\n"
                    )
                },
                {
                    "type": "Progress Check",
                    "learner": "How do I track my learning progress?",
                    "assistant": (
                        "You can view your progress in the **Progress Overview** section of your dashboard, learner. "
                        "It visually tracks completion of LinkedIn Learning, AI interactions, coaching, and discussions. "
                        "You'll also see your **Leadership Development Index** - a radar chart showing growth in Self, People, and Change Leadership. "
                    )
                },
                {
                    "type": "Motivation",
                    "learner": "I'm struggling to stay consistent with my learning.",
                    "assistant": (
                        "That's completely normal, learner - consistency builds mastery. "
                        "Consider setting a short learning window daily or using reminders in your **Task Centre**. "
                        "Remember, consistency unlocks the **Momentum Keeper** badge - awarded to those who keep learning without breaking their streak. "
                    )
                },
                {
                    "type": "Out-of-Scope Redirect",
                    "learner": "Can you suggest meditation practices to relax?",
                    "assistant": (
                        "I appreciate your focus on well-being, learner. "
                        "My role is to support your journey within the Foundational Leadership Programme at Petronas. "
                        "For wellness or meditation practices, I'd recommend exploring Petronas' Employee Well-being Resources or consulting a professional. "
                    )
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