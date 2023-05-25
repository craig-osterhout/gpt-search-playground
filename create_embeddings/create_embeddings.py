import os, sys
import pinecone
import requests
import hashlib
from bs4 import BeautifulSoup
import openai
from sitemapparser import SiteMapParser
import time
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import re


if len(sys.argv) != 2 or (str(sys.argv[1]) != "build" and str(sys.argv[1]) != "update"):
    print("Usage: python create_embeddings.py build|update")
    sys.exit()



# download stopwords and punctuation
nltk.download('stopwords')
nltk.download('punkt')
stop_words = set(stopwords.words('english'))

# Get the urls from the sitemap
sitemap="https://docs.docker.com/sitemap.xml"
urls = SiteMapParser(sitemap).get_urls()

# Set OpenAI embeddings model
openai.api_key = os.environ.get('OPENAI_API_KEY')
model_id = "text-embedding-ada-002"

# Connect to Pinecone
print("Connecting to Pinecone...")
environment="us-west1-gcp-free"
index_name = "docker-docs-index"
dimension=1536
pinecone.init(api_key=os.environ.get('PINECONE_API_KEY'),environment=environment)

# Delete and recreate the index if building
if sys.argv[1] == "build":
    if index_name in pinecone.list_indexes():
        print("Deleting index...")
        #pinecone.delete_index(index_name)
    print("Creating index...")
    #pinecone.create_index(index_name, metric="cosine", dimension=dimension)

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
    response = requests.get(str(url.loc))
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


#connect to pinecone
pinecone_index = pinecone.Index(index_name)

# If updating, delete the nodes associated with changed pages
if sys.argv[1] == "update":
    updated_urls = []
    for node in nodes:
        if id not in pinecone_index.ids(): #something changed
            pinecone_index.delete(filter={"url": str(node["url"])}) #delete the old nodes
            updated_urls.append(url)
    for node in nodes:
        if node["url"] not in updated_urls:
            nodes.remove(node)

#Get embeddings from OpenAI and add/update nodes in Pinecone
print("Adding/updating nodes...")
records={}
for node in nodes:
    heading=str(node["heading"])
    url = str(node["url"])
    text = str(node["text"])
    id = node["hash"]
    metadata = {"url": url, "text": text, "heading": heading}
    success=False
    while not success:
        try:
            embedding=openai.Embedding.create(input=text, model=model_id).data[0].embedding
            success=True
        except Exception as e:
            print(e)
            time.sleep(20)
    records.append({'id': id, 'values': embedding.tolist(), 'metadata': metadata})
    #records = [(id, embedding, metadata)]
pinecone_index.upsert(vectors=records)

