This repo may or may not work. I use it to experiment with different things and to keep checkpoints.

1. Clone this repo.

2. Create a Free Pinecone account, and a (Free for a month) OpenAI account.

3. Create `.env` file in each folder (create_embeddings and query) with your `OPENAI_API_KEY`, `OPENAI_API_BASE`, and `PINECONE_API_KEY`.
   You're responsible for any credit usage. This app may not be optimized to minimize credit usage.
   Note: Currently it doesn't use OpenAI to create embeddings, so you only get billed for chat completions

4. A lot of things may or may not be commented out depending on what I was testing. Look at what's commented and maybe uncomment it.

5. In the create_embedding directory, run:
   ```
   docker compose run --build --rm app
   ```
   Note: Make sure you have no index in pinecone because you only get 1 free 1, and uncomment the create index line.

6. After the index is built, in the query directory, run:
   ```
   docker compose run --build --rm app
   ```
7. Ask questions.