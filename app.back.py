import json
import requests
from bs4 import BeautifulSoup
from llama_index import (
     GPTVectorStoreIndex,
     ServiceContext,
     LLMPredictor,
     PromptHelper,
     Document,
     download_loader
     )
from llama_index.vector_stores import PineconeVectorStore
from llama_index.node_parser import SimpleNodeParser
from llama_index.storage.storage_context import StorageContext
from langchain import OpenAI
import urllib.request
import xml.etree.ElementTree as ET
import os
import sys
from datetime import datetime
import time
import pinecone
import supabase



def load_documents_to_gpt_vectorstore(urls):
    BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
    loader = BeautifulSoupWebReader()
    documents = loader.load_data(urls)
    parser = SimpleNodeParser()
    nodes = parser.get_nodes_from_documents(documents)
    max_input_size = 1024
    num_output = 256
    max_chunk_overlap = 20
    chunk_size_limit = 1000
    api_key = os.environ.get('OPENAI_API_KEY')
    llm_predictor = LLMPredictor(
        llm=OpenAI(
            temperature=0, model_name="embedding-ada-002", openai_api_key=api_key
        )
    )

    prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap, chunk_size_limit)

    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor, prompt_helper=prompt_helper
    )

    environment="us-west1-gcp-free"
    index_name = "docker-docs-index"
    dimension=1536
    pinecone.init(api_key=os.environ.get('PINECONE_API_KEY'), environment=environment)
    if index_name in pinecone.list_indexes():
        # Delete the index
        pinecone.delete_index(index_name)
    pinecone.create_index(index_name, metric="cosine", dimension=dimension)
    pinecone_index = pinecone.Index(index_name)
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index,
        environment=environment
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = GPTVectorStoreIndex.from_documents(documents, storage_context=storage_context, service_context=service_context)




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


def chat():
    while True:
        query = input("What would you like to chat about? ")
        get_answer(query)
        user_input = input("Type 'quit' to exit, or press enter to continue: ")
        if user_input.lower() == "quit":
            break


def get_answer(query):
    environment="us-west1-gcp-free"
    index_name = "docker-docs-index"
    dimension=1536
    pinecone.init(api_key=os.environ.get('PINECONE_API_KEY'), environment=environment)
    pinecone_index = pinecone.Index(index_name)
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index,
        environment=environment
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = GPTVectorStoreIndex([], storage_context=storage_context)

    query_engine = index.as_query_engine(similarity_top_k=10)
    response = query_engine.query(query)

    #response = index.query(query, similarity_top_k=10)
    print(response)
    for node in response.source_nodes:
        url = node.node.extra_info.get('URL')
        if url:
            print(url)
    return response




def array_to_file(arr, file):
    with open(file, "w") as f:
        for row in arr:
            f.write(row + "\n")


def file_to_array(file):
    with open(file, "r") as f:
        arr = []
        for line in f:
            line = line.rstrip('\n')
            arr.append(line)
    return arr



def build_index_sitemap(site, url_file, modified_after=None):
    sitemap= site + "/sitemap.xml"
    url_array = get_sitemap_urls(sitemap, modified_after)
    #array_to_file(url_array, url_file)

    urls = file_to_array(url_file)
    load_documents_to_gpt_vectorstore(urls)



def main():
    site = "https://docs.docker.com"
    data_folder = "/usr/src/app/data/"
    indices = "urls.txt"
    indices_path = data_folder + indices

    build_index_sitemap(site, indices_path)
    #chat()

if __name__ == "__main__":
    main()