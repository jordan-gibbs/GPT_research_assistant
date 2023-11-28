# GPT Research Assistant

## Overview
Build your own AI research assistant using the OpenAI Assistants API to access the latest AI research papers.

### The Challenge
- AI advancements are rapid and hard to track.
- Common issues include information overload and unreliable sources.
- Solution: Utilize open-source research papers from arXiv.org.

## arXiv.org Overview
- arXiv is a curated research-sharing platform hosting over two million scholarly articles.
- Offers recent and groundbreaking research in various fields, including AI.

## Building Your Assistant
### Prerequisites
- Python & your preferred Python IDE.
- Access to OpenAI Assistants API.
- Necessary Python libraries: `pandas`, `openai`, `arxivscraper`.

### Setup
1. **Install Libraries:** `pip install pandas openai arxivscraper`.
2. **arXiv Scraper Code**: Python code to scrape AI-related articles.
   - Adjust the date range as needed.
   - Saves data in `ARXIV/arxiv_data.json`.

### Creating the GPT Research Assistant
- Functions to upload files, setup the assistant, send messages, and run the assistant.
- Additional functions for saving sessions, displaying past sessions, and collecting message history.
- User-friendly interface for interacting with the assistant.

### Usage
1. Run the `main_loop()` function.
2. Choose to create a new agent or load an existing session.
3. Interact with the assistant, focusing on your chosen AI topics.

### Exit and Save
- Type 'exit' to end your session.
- Saves your chat history to a text file.

## Conclusion
- Ideal for keeping up with the latest in AI or any other field.
- Potential for daily automation and email debriefs.
