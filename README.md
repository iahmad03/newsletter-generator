# Newsletter Generator

A Python newsletter generator that scrapes RSS feeds, summarizes the content using the Hugging Face BART model, and outputs a clean HTML newsletter using a template.

This project currently fetches tech news but can be adapted to any RSS feed. Articles are summarized and output as a `index.html` file using a template, creating a simple and readable newsletter.

## Features

-   Scrapes articles from ([RSS feeds](https://rss.com/blog/how-do-rss-feeds-work/))
-   Summarizes content using the Hugging Face BART model
-   Easily customizable for other news sources or RSS feeds

## Setup

1. Clone this repository
2. Run `pip install -r requirements.txt` to install dependencies
3. Add your Hugging Face API key
    - Create a `.env` file in the root folder:
        - `HF_API_KEY=your_huggingface_api_key`
