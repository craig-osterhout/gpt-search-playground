This repo may or may not work. I use it to experiment with different things and to keep checkpoints.

## Create embeddings

1. Clone this repo. Make sure you switch to the correct branch.

2. Create a paid (free for a month) OpenAI account.

3. Create `.env` file in the `create_embedding` directory with the following:
   - OPENAI_API_KEY
   - OPENAI_API_BASE
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - POSTGRES_DB
   
   You're responsible for any openai API credit usage.  It currently costs around $0.50 to create all embeddings for docs.docker.com

4. In the create_embedding directory, run:
   ```
   MODE=build docker compose up --build
   ```
  Note: To update embeddings, run `MODE=update docker compose up --build`. Currently not implemented.

It takes over an hour to build the entire index. Sit back, relax and hope openai doesn't die.

## Query

1. Clone this repo.

2. Create the embeddings if you haven't already.

3. Create `.env` file in the `query` directory with the following:
   - OPENAI_API_KEY
   - OPENAI_API_BASE
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - POSTGRES_DB

4. In the `query` directory, run:
   `docker compose up --build`

5. Query the function.
  `curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"query":"what is docker"}'`
