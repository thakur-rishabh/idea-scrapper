import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy"))

async def evaluate_idea(text: str, title: str, source_url: str, topic: str = None) -> dict:
    """
    Evaluates a scraped post to see if it's a business idea.
    If 'topic' is provided, ensures the idea relates to the topic.
    Returns a dict with 'is_idea', 'summary', 'target_audience', 'score'.
    """
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "dummy":
        # Fallback if no API key is set
        print("No OpenAI API key found, using fallback for evaluation.")
        topic_str = f" about {topic}" if topic else ""
        return {
            "is_idea": True,
            "summary": f"Fallback summary of{topic_str}: {title}",
            "target_audience": "General public",
            "score": 75
        }

    topic_instruction = ""
    if topic:
        topic_instruction = f"\n    CRITICAL REQUIREMENT: This idea MUST be strictly related to the topic: '{topic}'. If it is NOT related to '{topic}', set 'is_idea' to false."

    prompt = f"""
    Analyze the following post from the internet:
    Title: {title}
    URL: {source_url}
    Content: {text}

    Determine if this post contains a valid business or app idea. 
    If it is NOT an idea (e.g., it's just a general question or unrelated topic), set 'is_idea' to false.{topic_instruction}
    If it IS an idea, provide a clear summary, the potential target audience, and a confidence score from 0-100 on how viable or well-defined the idea is.

    Return the response as JSON exactly matching this format:
    {{
        "is_idea": bool,
        "summary": "string",
        "target_audience": "string",
        "score": integer
    }}
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert startup advisor and AI parser. You only reply in strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error evaluating idea: {e}")
        return {
            "is_idea": True,
            "summary": f"Fallback idea summary due to API error: {title}",
            "target_audience": "Founders",
            "score": 80
        }

async def generate_random_idea() -> dict:
    """
    Generates a completely random startup/business idea using the LLM.
    """
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "dummy":
        return {
            "is_idea": True,
            "summary": "Fallback random idea: A smart toaster that prints the day's weather on your bagel.",
            "target_audience": "Breakfast lovers",
            "score": 88
        }

    prompt = """
    You are an expert startup founder and brainstormer. Your task is to generate a highly creative, unique, and actionable startup or business idea. 
    It should not be a trivial idea, but something solving a real problem for a specific niche. 
    
    Return the response as JSON exactly matching this format:
    {
        "is_idea": true,
        "summary": "string",
        "target_audience": "string",
        "score": integer
    }
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You only reply in strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error generating random idea: {e}")
        return {
            "is_idea": True,
            "summary": "Fallback random idea generated due to API error.",
            "target_audience": "Founders",
            "score": 85
        }
