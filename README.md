This repo may or may not work. I use it to experiment with different things and to keep checkpoints.

## Create embeddings

1. Clone this repo. Make sure you switch to the correct branch.

2. Create a free Pinecone account, and a paid (free for a month) OpenAI account.

3. Create `.env` file in the `create_embedding` directory with your `OPENAI_API_KEY`, `OPENAI_API_BASE`, and `PINECONE_API_KEY`.
   You're responsible for any openai API credit usage. This app may not be optimized to minimize credit usage. It currently costs around $0.50 to create all embeddings for docs.docker.com

4. Using the Pinecone console, create a Pinecone index called "docker-docs-index". Or uncomment the following lines in the script to create one when running the script. 
   `pinecone.create_index(index_name, metric="cosine", dimension=dimension)`

5. In the create_embedding directory, run:
   ```
   docker compose run --build --rm app
   ```

It takes over an hour to build the entire index. Sit back, relax and hope your connection doesn't die.

## Query

1. Clone this repo.

2. Create the embeddings if you haven't already.

3. Create `.env` file in the `query` directory with your `OPENAI_API_KEY`, `OPENAI_API_BASE`, and `PINECONE_API_KEY`.
   You're responsible for any openai API credit usage. This app may not be optimized to minimize credit usage. Assume each query costs $0.01

4. In the `query` directory, run:
   `docker compose up --build`

5. Query the function.
  `curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"query":"what is docker"}'`


Deploy the query to Lamdba, and attach an API Gateway.

Todo:
 - Update create_embeddings to only update the delta, or the entire index based on parameters.
