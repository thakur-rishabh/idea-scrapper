import asyncio
import requests
from sqlalchemy import Engine
from sqlmodel import Session, select
from models import Idea
from ai_processor import evaluate_idea

REQUEST_TIMEOUT = 10  # seconds

def fetch_hn_ask_stories(topic: str = None):
    """Fetch Ask HN stories. If topic is provided, use Algolia search, else get recent."""
    try:
        stories = []
        if topic:
            url = f"https://hn.algolia.com/api/v1/search?query={topic}&tags=ask_hn"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            hits = response.json().get("hits", [])
            for hit in hits[:30]:
                if hit.get("title") and hit.get("story_text"):
                    stories.append({
                        "id": hit.get("objectID"),
                        "title": hit.get("title"),
                        "text": hit.get("story_text")
                    })
        else:
            response = requests.get(
                "https://hacker-news.firebaseio.com/v0/askstories.json",
                timeout=REQUEST_TIMEOUT,
            )
            story_ids = response.json()
            for sid in story_ids[:15]:
                story_resp = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    timeout=REQUEST_TIMEOUT,
                )
                story = story_resp.json()
                if story and story.get("title") and story.get("text"):
                    stories.append(story)
        return stories
    except Exception as e:
        print(f"Error fetching from HN: {e}")
        return []

async def process_stories(session: Session, stories, topic: str = None):
    for story in stories:
        url = f"https://news.ycombinator.com/item?id={story['id']}"

        statement = select(Idea).where(Idea.source_url == url)
        existing = session.exec(statement).first()
        if existing:
            continue

        print(f"Evaluating: {story.get('title')}")
        evaluation = await evaluate_idea(story.get("text", ""), story.get("title", ""), url, topic=topic)

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

async def run_scraper_async(engine: Engine, topic: str = None):
    print(f"Starting Hacker News Scraper... Topic: {topic if topic else 'General'}")
    stories = fetch_hn_ask_stories(topic=topic)
    if not stories:
        print("No stories found.")
        return
    # Own session so it's not tied to the HTTP request lifecycle
    with Session(engine) as session:
        await process_stories(session, stories, topic=topic)
    print("Scraping completed.")

def run_all_scrapers(engine: Engine, topic: str = None):
    """Entry point for background tasks — always creates a fresh event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_scraper_async(engine, topic=topic))
    finally:
        loop.close()

if __name__ == "__main__":
    from database import engine as db_engine, create_db_and_tables
    create_db_and_tables()
    run_all_scrapers(db_engine)
