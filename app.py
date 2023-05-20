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
from sentence_transformers import SentenceTransformer # Import 

# Initialize OpenAI API client
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_client = supabase.Client(supabase_url, supabase_key)






# Define a function to ask a question and get an answer from OpenAI using the documents as context
def ask(question):
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2') # You can choose any model from https://huggingface.co/sentence-transformers
    embedding=model.encode(question) # Use sentence-transformers model to create embeddings
    print(embedding)
    #embedding = query_embedding["data"][0]["embedding"]

    result = supabase_client.rpc("get_docs",{"query_embedding": embedding}
    ).execute()


    # Extract the titles and contents of the documents
    text = [row["text"] for row in result.data]
    urls = [row["url"] for row in result.data]

    text = " ".join(text) # Join the strings in the text list with spaces
    words = text.split()
    words = words[:500]
    text = " ".join(words)



    # Query OpenAI with the question and the context and get an answer
    answer = openai.Completion.create(
        engine="davinci",
        prompt=f"{text}\n\nQ: {question}\nA:",
        max_tokens=1000,
        temperature=0,
        stop="\n"
    )["choices"][0]["text"]

    # Return the answer
    return answer, urls

# Test the function with some questions
answer, sources= ask("What is Docker?")
print (answer)
print (sources)


answer, sources= ask("What is the latest version of Docker Desktop?")
print (answer)
print (sources)