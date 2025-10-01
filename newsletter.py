import feedparser as fp
import requests
import os
import logging
import random
from feeds import FEEDS
from newspaper import Article
from dotenv import load_dotenv

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    raise ValueError("Hugging Face API key not found")

HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Summarization params
MAX_LEN = 180 
MIN_LEN = 100 

CHUNK_SIZE = 600 # do not modify this line
CHUNK_MAX_LEN = 140
CHUNK_MIN_LEN = 100

NUM_ARTICLES = 3  # Number of articles to pick randomly


def fetch_articles() -> list[dict]:
    all_entries = []

    for source, feed_url in FEEDS.items():
        feed = fp.parse(feed_url)
        for entry in feed.entries:
            all_entries.append({
                "link": entry.link,
                "title": entry.get("title", "No Title"),
                "published": entry.get("published", "No Date")
            })

    if len(all_entries) > NUM_ARTICLES:
        selected_entries = random.sample(all_entries, NUM_ARTICLES)
    else:
        selected_entries = all_entries

    articles = []
    for entry in selected_entries:
        try:
            art = Article(entry["link"])
            art.download()
            art.parse()
            published = art.publish_date.strftime("%B %d, %Y") if art.publish_date else entry["published"] # type: ignore
            articles.append({
                "link": entry["link"],
                "title": art.title or entry["title"],
                "published": published,
                "full_text": art.text
            })
        except Exception as e:
            logging.warning(f"Failed to fetch article {entry['link']}: {e}")
            continue

    return articles


def hf_summarize(text: str, max_len: int, min_len: int) -> str:
    payload = {"inputs": text, "parameters": {"max_length": max_len, "min_length": min_len}}
    
    try:
        response = requests.post(HF_API_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()[0]["summary_text"]
    except Exception as e:
        logging.warning(f"Error summarizing text: {e}")
        return "[Error summarizing]"


def summarize_articles(full_articles: list[dict]) -> list[dict]:
    summarized_articles = []
    
    for art in full_articles:
        words = art["full_text"].split()
        if len(words) <= CHUNK_SIZE:
            summary = hf_summarize(art["full_text"], MAX_LEN, MIN_LEN)
        else:
            chunk_summaries = []
            for i in range(0, len(words), CHUNK_SIZE):
                chunk = " ".join(words[i:i + CHUNK_SIZE])
                chunk_summary = hf_summarize(chunk, CHUNK_MAX_LEN, CHUNK_MIN_LEN)
                chunk_summaries.append(chunk_summary)
            combined_text = " ".join(chunk_summaries)
            summary = hf_summarize(combined_text, MAX_LEN, MIN_LEN)

        summarized_articles.append({
            "link": art["link"],
            "title": art.get("title", "No Title"),
            "published": art.get("published", "No Date"),
            "summary": summary
        })
        
    return summarized_articles


def build_html(articles: list[dict]) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "templates", "base.html")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_template = f.read()
    except Exception as e:
        logging.error(f"Could not read template: {e}")
        raise

    article_block = """
        <a class="article-card" href="{link}" target="_blank">
            <div class="content">
                <div class="date">{published}</div>
                <h2>{title}</h2>
                <p>{summary}</p>
            </div>
        </a>
    """

    articles_html = "\n".join(
        article_block.format(
            title=a.get("title", "No Title"),
            published=a.get("published", "No Date"),
            summary=a["summary"],
            link=a["link"]
        ) for a in articles
    )

    return html_template.replace("{articles}", articles_html)


def main():
    logging.info("Fetching articles...")
    full_articles = fetch_articles()
    logging.info(f"Fetched articles")

    logging.info("Summarizing articles...")
    summarized_articles = summarize_articles(full_articles)

    logging.info("Building HTML...")
    html_content = build_html(summarized_articles)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "newsletter.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logging.info(f"Newsletter saved to {output_path}")


if __name__ == "__main__":
    main()
