# Import libraries
import os
import sys
import supabase
import llama_index
from bs4 import BeautifulSoup
from llama_index import (
     download_loader,
     GPTVectorStoreIndex,
     PromptHelper,
     LLMPredictor,
     ServiceContext
     )
from llama_index.node_parser import SimpleNodeParser
from sentence_transformers import SentenceTransformer # Import sentence-transformers library
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import time

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_client = supabase.Client(supabase_url, supabase_key)



def get_sitemap_urls(site, modified_after=None):
    response = urllib.request.urlopen(site)
    sitemap_xml = response.read()

    root = ET.fromstring(sitemap_xml)

    urls = []
    for url_elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        lastmod_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
        lastmod_str = lastmod_elem.text if lastmod_elem is not None else ""
        lastmod = datetime.fromisoformat(lastmod_elem.text.rstrip('Z'))

        if modified_after is None or lastmod >= datetime.fromisoformat(modified_after):
            urls.append(loc_elem.text)
    return urls


data_folder = "/usr/src/app/data/"
indices = "urls.txt"
file = data_folder + indices
site="https://docs.docker.com"
sitemap= site + "/sitemap.xml"
urls = []
#with open(file, "r") as f:
#    for line in f:
#        line = line.rstrip('\n')
#        urls.append(line)
BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
loader = BeautifulSoupWebReader()
documents=[]
urls = get_sitemap_urls(sitemap)

documents = loader.load_data(urls)
parser = SimpleNodeParser()
nodes = parser.get_nodes_from_documents(documents)



# Load sentence-transformers model
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2') # You can choose any model from https://huggingface.co/sentence-transformers


data = supabase_client.table("docs").delete().gt("id", 0).execute()




# Insert the documents and embeddings into the table
for node in nodes:
    text =  node.text
    url = node.extra_info["URL"]
    embedding=model.encode(text) # Use sentence-transformers model to create embeddings
    data= supabase_client.table("docs").insert({
        "text": text,
        "url": url,
        "embedding": embedding.tolist() # Convert numpy array to list for database insertion
    }).execute()
