import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy"))

# Truncate scraped text to avoid excessive token usage and potential injection payloads
MAX_TEXT_CHARS = 2000

def _truncate(text: str) -> str:
    if len(text) > MAX_TEXT_CHARS:
        return text[:MAX_TEXT_CHARS] + "... [truncated]"
    return text

def _no_api_key() -> bool:
    key = os.getenv("OPENAI_API_KEY")
    return not key or key == "dummy"

async def evaluate_idea(text: str, title: str, source_url: str, topic: str = None) -> dict:
    """
    Evaluates a scraped post to see if it's a business idea.
    If 'topic' is provided, ensures the idea relates to the topic.
    Returns a dict with 'is_idea', 'summary', 'target_audience', 'score'.
    """
    if _no_api_key():
        print("No OpenAI API key found — skipping evaluation.")
        return {"is_idea": False, "summary": "", "target_audience": "", "score": 0}

    topic_instruction = ""
    if topic:
        topic_instruction = (
            f"\nCRITICAL REQUIREMENT: This idea MUST be strictly related to the topic: '{topic}'. "
            f"If it is NOT related to '{topic}', set 'is_idea' to false."
        )

    # Sanitise user-supplied content into dedicated message fields to reduce prompt injection risk
    user_message = (
        f"Title: {_truncate(title)}\n"
        f"URL: {source_url}\n"
        f"Content:\n{_truncate(text)}"
    )

    system_message = (
        "You are an expert startup advisor and AI parser. You only reply in strict JSON.\n"
        "Determine if the post contains a valid business or app idea.\n"
        "If it is NOT an idea (e.g., just a general question or unrelated topic), set 'is_idea' to false."
        + topic_instruction +
        "\nIf it IS an idea, provide a clear summary, the potential target audience, and a confidence "
        "score from 0-100 on how viable or well-defined the idea is.\n"
        'Return JSON exactly: {"is_idea": bool, "summary": "string", "target_audience": "string", "score": integer}'
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error evaluating idea: {e}")
        # Return is_idea=False so errors don't produce phantom ideas
        return {"is_idea": False, "summary": "", "target_audience": "", "score": 0}

async def generate_random_idea() -> dict:
    """
    Generates a completely random startup/business idea using the LLM.
    """
    if _no_api_key():
        return {
            "is_idea": True,
            "summary": "Fallback random idea: A smart toaster that prints the day's weather on your bagel.",
            "target_audience": "Breakfast lovers",
            "score": 88
        }

    prompt = (
        "Generate a highly creative, unique, and actionable startup or business idea. "
        "It should solve a real problem for a specific niche — not a trivial concept.\n"
        'Return JSON exactly: {"is_idea": true, "summary": "string", "target_audience": "string", "score": integer}'
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert startup founder and brainstormer. You only reply in strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error generating random idea: {e}")
        return {"is_idea": False, "summary": "", "target_audience": "", "score": 0}
