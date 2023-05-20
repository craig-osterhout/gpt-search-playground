# Import libraries
import os
import sys
import openai
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
from langchain import OpenAI
from llama_index import OpenAIEmbedding
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import time

# Load environment variables
#from dotenv import load_dotenv
#load_dotenv()

# Initialize OpenAI API client
#api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")

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
documents = loader.load_data(get_sitemap_urls(sitemap))
parser = SimpleNodeParser()
nodes = parser.get_nodes_from_documents(documents)



#llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-embedding-ada-002", openai_api_key=api_key))

max_input_size = 4096
num_output = 256
max_chunk_overlap = 20
chunk_size_limit = 1000
prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap, chunk_size_limit)

#service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)



#index = GPTVectorStoreIndex(nodes, service_context=service_context)

data = supabase_client.table("docs").delete().gt("id", 0).execute()




# Insert the documents and embeddings into the table
for node in nodes:
    text =  node.text
    url = node.extra_info["URL"]
    embed_model=OpenAIEmbedding()
    embedding=embed_model.get_text_embedding(node.text)
    data= supabase_client.table("docs").insert({
        "text": text,
        "url": url,
        "embedding": embedding
    }).execute()

