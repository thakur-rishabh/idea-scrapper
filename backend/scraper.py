import json
import asyncio
import requests
from sqlmodel import Session
from models import Idea
from ai_processor import evaluate_idea

def fetch_hn_ask_stories(topic: str = None):
    """Fetch Ask HN stories. If topic is provided, use Algolia search, else get recent."""
    try:
        stories = []
        if topic:
            # Algolia Search API for Hacker News
            # Filter by Ask HN and the specific query
            url = f"https://hn.algolia.com/api/v1/search?query={topic}&tags=ask_hn"
            response = requests.get(url)
            hits = response.json().get("hits", [])
            for hit in hits[:30]:
                if hit.get("title") and hit.get("story_text"):
                    stories.append({
                        "id": hit.get("objectID"),
                        "title": hit.get("title"),
                        "text": hit.get("story_text")
                    })
        else:
            # Get latest ask stories
            response = requests.get("https://hacker-news.firebaseio.com/v0/askstories.json")
            story_ids = response.json()
            
            # Fetch top 15 to avoid excessive API calls
            for sid in story_ids[:15]:
                story_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                story = story_resp.json()
                # Only process stories that have text (some are just titles)
                if story and story.get("title") and story.get("text"):
                    stories.append(story)
        return stories
    except Exception as e:
        print(f"Error fetching from HN: {e}")
        return []

async def process_stories(session: Session, stories, topic: str = None):
    for story in stories:
        url = f"https://news.ycombinator.com/item?id={story['id']}"
        
        # Check if already exists in DB
        from sqlmodel import select
        statement = select(Idea).where(Idea.source_url == url)
        existing = session.exec(statement).first()
        
        if existing:
            continue
            
        print(f"Evaluating: {story.get('title')}")
        # Evaluate with AI, passing the topic
        evaluation = await evaluate_idea(story.get("text", ""), story.get("title", ""), url, topic=topic)
        
        # If the AI thinks it's an idea (or fallback mechanism applies)
        if evaluation.get("is_idea", False) and evaluation.get("score", 0) > 40:
            idea = Idea(
                title=story.get("title"),
                summary=evaluation.get("summary"),
                source_url=url,
                original_text=story.get("text"),
                score=evaluation.get("score"),
                target_audience=evaluation.get("target_audience", ""),
                status="pending"
            )
            session.add(idea)
            session.commit()
            print(f"Added new idea: {idea.title} with score {idea.score}")

async def run_scraper_async(session: Session, topic: str = None):
    print(f"Starting Hacker News Scraper... Topic: {topic if topic else 'General'}")
    stories = fetch_hn_ask_stories(topic=topic)
    if not stories:
        print("No stories found.")
        return
    await process_stories(session, stories, topic=topic)
    print("Scraping completed.")

def run_all_scrapers(session: Session, topic: str = None):
    """Entry point for background tasks"""
    # Create a new event loop for the background thread if necessary
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(run_scraper_async(session, topic=topic))

if __name__ == "__main__":
    # For manual testing
    from database import get_session, create_db_and_tables
    create_db_and_tables()
    # get a session
    gen = get_session()
    sess = next(gen)
    try:
        run_all_scrapers(sess)
    finally:
        sess.close()
