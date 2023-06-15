This implements an ai-assisted search function for docker docs.


It scrapes the docs.docker.com website.
It uses openai to create embeddings for each heading.
It stores the embeddings in a postgresql database using pgvector.
When someone searches, it creates an embedding of their search query.
It does a vector similarity search to find the top 5 most similar sections in the database.
It passes those sections, the user query, and some instruction prompts to openai chat completion.
It returns an answer based on the instruction prompts.


## Create embeddings

1. Clone this repo.

2. Create a paid (free for a month) OpenAI account.

3. Create `.env` file in the `open-ai-create_embedding` directory with the following:
   - OPENAI_API_KEY
   - OPENAI_API_BASE
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - POSTGRES_DB

   For example:
   ```
   OPENAI_API_KEY=123456
   OPENAI_API_BASE=https://api.openai.com/v1
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=ins3cure
   POSTGRES_DB=docker-docs
   ```

   You're responsible for any openai API credit usage.  It currently costs around $0.50 to create all embeddings for docs.docker.com

4. In the `open-ai-create_embedding` directory, run:
   ```
   MODE=build docker compose up --build
   ```

   Sit back, relax. It takes over an hour to build the entire index.

5. The app container will stop when it's done. Bring down the database container if you'll run a query because its compose stack recreates the database container. Use control+c if attached, or `docker compose down`.

## Query

1. Clone this repo.

2. Create the embeddings if you haven't already.

3. Create `.env` file in the `open-ai-query` directory with the following:
   - OPENAI_API_KEY
   - OPENAI_API_BASE
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - POSTGRES_DB

   For example:
   ```
   OPENAI_API_KEY=123456
   OPENAI_API_BASE=https://api.openai.com/v1
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=ins3cure
   POSTGRES_DB=docker-docs
   ```

4. In the `open-ai-query` directory, run:
   `docker compose up --build`

5. Query the function in another terminal.
  `curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"query":"what is docker"}'`


## Todo
 - SAM deploy
 - Code cleanup
 - Better error handling
 - Frontend for docs
 - Optimize embeddings and embedding search
   - Two-pass search? First get 10 most similar pages based on the entire page's context. Then within those, get 5 most similar sections.
   - Implement `Mode=update` for embedding creation.