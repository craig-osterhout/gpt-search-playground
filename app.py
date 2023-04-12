import json
import requests
from bs4 import BeautifulSoup
from llama_index import (
     GPTSimpleVectorIndex,
     ServiceContext,
     LLMPredictor,
     PromptHelper,
     Document,
     download_loader
)
from llama_index.node_parser import SimpleNodeParser
from langchain import OpenAI
import urllib.request
import xml.etree.ElementTree as ET
import os
import sys
from datetime import datetime
import time


def load_documents_to_gpt_vectorstore(urls):
    BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
    loader = BeautifulSoupWebReader()
    documents = []
    for url in urls:
        url_array = []
        url_array.append(url)
        documents.append(loader.load_data(url_array))
        print(url)
        time.sleep(5) # add a delay of 1 second between loading webpages
    parser = SimpleNodeParser()

    nodes = parser.get_nodes_from_documents(documents)
    max_input_size = 4096
    num_output = 256
    max_chunk_overlap = 20
    api_key = os.environ.get('OPENAI_API_KEY')
    llm_predictor = LLMPredictor(
        llm=OpenAI(
            temperature=0, model_name="text-davinci-003", openai_api_key=api_key
        )
    )

    prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)

    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor, prompt_helper=prompt_helper
    )
    index = GPTSimpleVectorIndex(nodes, service_context=service_context)
    index.save_to_disk("/usr/src/app/data/gpt_index_docs.json")
    return index


def scrape(site):
    urls = []
    def scrape_helper(current_site):
        nonlocal urls

        r = requests.get(current_site)

        s = BeautifulSoup(r.text, "html.parser")
        #print(s.find_all("a"))
        for i in s.find_all("a"):
                if "href" in i.attrs:
                    href = i.attrs["href"]

                    if href.startswith("/") or href.startswith("#"):
                            full_url = site + href

                            print(full_url)
                            if full_url not in urls:
                                 urls.append(full_url)
                                 scrape_helper(full_url)
    scrape_helper(site)
    return urls



def get_sitemap_urls(site, modified_after=None):

    response = urllib.request.urlopen(site)
    sitemap_xml = response.read()

    root = ET.fromstring(sitemap_xml)

    urls = []

    for sitemap_elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
        sitemap_url_elem = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        sitemap_url = sitemap_url_elem.text

        response = urllib.request.urlopen(sitemap_url)
        sitemap_xml = response.read()

        sitemap_root = ET.fromstring(sitemap_xml)

        for url_elem in sitemap_root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
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
    index = GPTSimpleVectorIndex.load_from_disk("/usr/src/app/data/gpt_index_docs.json")
    response = index.query(query, similarity_top_k=10)
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
    array_to_file(url_array, url_file)

    urls = file_to_array(url_file)
    load_documents_to_gpt_vectorstore(urls)


def build_index_scrape(site, url_file):
    url_array = scrape(site)
    array_to_file(url_array, url_file)

    #urls = file_to_array(url_file)
    #load_documents_to_gpt_vectorstore(urls)


def main():
#   sites = ["https://docs.docker.com", "https://forums.docker.com"]
#   data_folder = "/usr/src/app/data/"
#   indices = ["urls.txt", "urls2.txt"]

   #chat()
#   build_index_sitemap("https://forums.docker.com", "/usr/src/app/data/urls2.txt", '2022-01-01')


if __name__ == "__main__":
    main()