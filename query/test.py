# Import libraries
import os,sys, time
import psycopg2
from psycopg2.sql import Identifier, SQL
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from accelerate import Accelerator # Import the Accelerator class

print("Starting...")

# Load the model
print("Loading the model...")

try:
    tokenizer = AutoTokenizer.from_pretrained('gpt2')

    model = AutoModelForCausalLM.from_pretrained('gpt2', low_cpu_mem_usage=True)
except Exception as e:
    print("Error loading model")
    print(e)