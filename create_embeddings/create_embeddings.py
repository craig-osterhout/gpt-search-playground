import os
import pinecone
import requests
import hashlib
from bs4 import BeautifulSoup
openai
from sitemapparser import SiteMapParser
import datetime
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import re



# download stopwords and punctuation
nltk.download('stopwords')
nltk.download('punkt')
stop_words = set(stopwords.words('english'))



# Get the urls from the sitemap
sitemap="https://docs.docker.com/sitemap.xml"
urls = SiteMapParser(sitemap).get_urls()
#urls = list(SiteMapParser(sitemap).get_urls())
#urls = [url for url in urls if url.loc.startswith("https://docs.docker.com/get-started/what-is-a-container")]



# Load sentence-transformers model
print("Loading model...")
#model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
#modelPath = "/usr/src/app/data/"
#model.save(modelPath) 
#model = SentenceTransformer(modelPath)
# Load OpenAI embeddings model
openai.api_key = os.environ.get('OPENAI_API_KEY')
model_id = "text-embedding-ada-002"



# Connect to Pinecone
print("Connecting to Pinecone...")
environment="us-west1-gcp-free"
index_name = "docker-docs-index"
dimension=768
pinecone.init(api_key=os.environ.get('PINECONE_API_KEY'),environment=environment)
#if index_name in pinecone.list_indexes():
#    print("Deleting index...")
#    pinecone.delete_index(index_name)
print("Creating scraping pages...")
#pinecone.create_index(index_name, metric="cosine", dimension=dimension)




nodes = []
modified_after = (datetime.datetime.now() - datetime.timedelta(days=10000)).isoformat()
for url in urls:
    lastmod = datetime.datetime.fromisoformat(str(url.lastmod).rstrip('Z')).replace(tzinfo=None)
    if lastmod <= datetime.datetime.fromisoformat(modified_after) or url.loc.startswith("https://docs.docker.com/contribute/"):
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

    for heading in headings:
        siblings = []
        sibling = heading.next_sibling
        while sibling and not (sibling.name in ["h1", "h2", "h3", "h4"]):
            if sibling.name in ["p", "ul", "ol", "div", "table", "pre", "blockquote", "code"]:
                siblings.append(sibling)
            sibling = sibling.next_sibling

        text = "\n".join([sibling.text for sibling in siblings])
        hash = hashlib.md5((heading.text + text).encode()).hexdigest()
        if text:
             # update the parents list according to the heading level
            level = int(heading.name[1])
            if level == 1:
                 parents = [heading.text]
            elif level > len(parents):
                parents.append(heading.text)
            else:
                parents = parents[:level-1] + [heading.text]

            # prepend the parent headings to the text
            prefix = " ".join(parents)
            text = prefix + " " + text
            text = text

            node = {"heading": heading.text, "url": str(url.loc), "text": text, "hash" : hash}
            nodes.append(node)




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


pinecone_index = pinecone.Index(index_name)



#Add new nodes. Delete and replace updated nodes.
print("Adding/updating nodes...")
for node in nodes:
    text = clean_text(node["text"])
    heading=node["heading"]
    url = node["url"]
    id = node["hash"]
    metadata = {"url": url, "text": text, "heading": heading}
    fetch_response = pinecone_index.fetch(ids=[id])
    if len(fetch_response["vectors"])>0: #change to zero when not testing
        nodes.remove(node)
    else:
        embedding=model.encode(text).tolist()
        #try to find the correct vector. It's not perfect.
        #Should do a complete rebuild periodically.
        query_result = pinecone_index.query(queries=[embedding], filter={"url": {"$eq": url}}, top_k=1)
        if query_result.results[0].ids:
            pinecone_index.delete([id])
        records = [(id, embedding, metadata)]
        print("Updating/Adding: " + url + " : " + heading)
        #pinecone_index.upsert(vectors=records)
