import os, sys
import requests
import hashlib
from bs4 import BeautifulSoup
from sitemapparser import SiteMapParser
import time
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import re
import psycopg2
from sentence_transformers import SentenceTransformer
import pgvector
from pgvector.psycopg2 import register_vector

#if len(sys.argv) != 2 or (str(sys.argv[1]) != "build" and str(sys.argv[1]) != #"update"):
#    print("Usage: python create_embeddings.py build|update")
#    sys.exit()

# download stopwords and punctuation
print("Downloading stopwords and punctuation...")
nltk.download('stopwords')
nltk.download('punkt')
stop_words = set(stopwords.words('english'))

# Get the urls from the sitemap
sitemap="https://docs.docker.com/sitemap.xml"
urls = SiteMapParser(sitemap).get_urls()

# define a function to clean a text
def clean_text(text):
  # tokenize the text
  text = text.replace('\n', ' ')
  tokens = word_tokenize(text)
  # filter out stopwords and numbers
  filtered_tokens = [token.lower() for token in tokens if token.lower() not in stop_words and not token.isdigit()]
  # join the tokens back to a string
  cleaned_text = ' '.join(filtered_tokens)
   # restore code blocks from placeholders
  return cleaned_text

# define a function to split a text into chunks of a given length
def split_by_length(text, width, overlap):
    width = max(1, width)
    overlap = max(0, overlap)
    words = text.split()
    chunks = []
    for i in range(0, len(words), width - overlap):
        chunk = words[i:i + width]
        chunks.append(chunk)
    return chunks


# Scrape all the pages and create nodes ready for embedding and indexing
nodes = []
for url in urls:
    if url.loc.startswith("https://docs.docker.com/search/"):
        continue
    print(str(url.loc))
    success = False
    attempts = 0
    max_attempts = 3
    while not success and attempts < max_attempts:
        try:
            response = requests.get(str(url.loc))
            success = True
        except requests.exceptions.RequestException as e:
            print(e)
            attempts += 1
            time.sleep(20)
    if response.history: #page redirects
        continue
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("main") is not None:
        main = soup.find("main")
    else:
        main = soup.find("body")
    headings = main.find_all(["h1", "h2", "h3", "h4"])

    # create a list to store the parent headings
    parents = []
    prefix=""

    for heading in headings:
        siblings = []
        sibling = heading.next_sibling
        while sibling and not (sibling.name in ["h1", "h2", "h3", "h4", "div"]):
            if sibling.name in ["p", "ul", "ol", "table", "pre", "blockquote", "code"]:
                siblings.append(sibling)
            sibling = sibling.next_sibling

        text = "\n".join([sibling.text for sibling in siblings])
        if text:
             # update the parents list according to the heading level
            level = int(heading.name[1])
            if level == 1:
                 parents = [heading.text]
            elif level > len(parents):
                parents.append(heading.text)
            else:
                parents = parents[:level-1] + [heading.text]

            #clean the text for unecessary words and characters
            text = clean_text(text)

             # split the node into multiple nodes that contain text less than 500 words each to avoid max tokens
            if len(text.split()) > 500:
                chunks = split_by_length(text, 500, 100)
                for chunk in chunks:
                    new_node_text_str = ' '.join(chunk)
                    # prepend the parent headings to the text
                    prefix = " ".join(parents)
                    new_node_text_str = prefix + " " + new_node_text_str
                    new_node_hash = hashlib.md5((heading.text + new_node_text_str).encode()).hexdigest()
                    new_node_dict = {"heading": str(heading.text), "url": str(url.loc), "text": new_node_text_str, "hash" : new_node_hash}
                    #print("Created chunk: " + str(url.loc) +" " + str(heading.text))
                    nodes.append(new_node_dict)
            else:
                prefix = " ".join(parents)
                text = prefix + " " + text
                hash = hashlib.md5((heading.text + text).encode()).hexdigest()
                #build the node
                node = {"heading": str(heading.text), "url": str(url.loc), "text": str(text), "hash" : hash}
                nodes.append(node)
                #print("Created: " + str(url.loc) +" " + str(heading.text))


# Get the password from an environment variable
password = os.environ.get("POSTGRES_PASSWORD")

# Connect to PostgreSQL database
conn = psycopg2.connect(host="postgres", dbname="docker-docs", user="postgres", password=password)
register_vector(conn)
cur = conn.cursor()


# Drop table if exists
cur.execute("DROP TABLE IF EXISTS items;")

# Create table with vector column
cur.execute("CREATE TABLE items (id text PRIMARY KEY, embedding vector(768), url text, heading text, text text);")
#cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
#cur.execute("CREATE INDEX IF NOT EXISTS idx_items_embedding ON items USING vector (embedding vector_ops);")

# Load sentence-transformers model
model = SentenceTransformer('/usr/src/app/models/')


# For each node, encode the text and insert the vector into the table
for node in nodes:
    print("Adding " + str(node["url"]) + " " + str(node["heading"]) + " to the database...")
    heading = str(node["heading"])
    url = str(node["url"])
    text = str(node["text"])
    id = node["hash"]
    embedding = model.encode(text)
    cur.execute("INSERT INTO items (id, embedding, url, heading, text) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET embedding = EXCLUDED.embedding;", (id, embedding, url, heading, text))

# Commit changes and close connection
conn.commit()
cur.close()
conn.close()
