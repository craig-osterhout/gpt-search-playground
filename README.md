This repo may or may not work. I use it to experiment with different things and to keep checkpoints.

## Create embeddings

1. Clone this repo. Make sure you switch to the correct branch.

2. Create a free Pinecone account, and a paid (free for a month) OpenAI account.

3. Create `.env` file in the `create_embedding` directory with your `OPENAI_API_KEY`, `OPENAI_API_BASE`, and `PINECONE_API_KEY`.
   You're responsible for any openai API credit usage.  It currently costs around $0.50 to create all embeddings for docs.docker.com

4. In the create_embedding directory, run:
   ```
   MODE=build docker compose up --build
   ```
  Note: To update embeddings, run `MODE=update docker compose up --build`

It takes over an hour to build the entire index. Sit back, relax and hope your connection doesn't die.

## Query

1. Clone this repo.

2. Create the embeddings if you haven't already.

3. Create `.env` file in the `query` directory with your `OPENAI_API_KEY`, `OPENAI_API_BASE`, and `PINECONE_API_KEY`.
   You're responsible for any openai API credit usage. Assume each query costs between $0.002 to $0.006, mostly depending on the length of the sources.

4. In the `query` directory, run:
   `docker compose up --build`

5. Query the function.
  `curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"query":"what is docker"}'`


Deploy the query to Lamdba, and attach an API Gateway.


## Back of the napkin calculations
These are based on words, not tokens. Tokens tend to be 2-3x the word count.

- Max word length of embedding: 500
- Median word length of all embeddings: 44
- Max user query: 256
- Instruction prompt: ~256

### Max cost for 1 query
( 4096 / 1000) * .002 = $0.008

### Cost of query based on median
((256 + (44 * 5)  + 256) / 1000) * .002 = $0.0015
(Increase 2-3x because tokens ~ .0030 ~ .0045)

### Cost per day based on **current** search usage
Minimum searches: 6000
Assuming max tokens for every search: 6000 * .008 = $48
Assuming median for every search: 6000 * .0015 = $9
  - (6000 * .003 = $18)
  - (6000 * .0045 = $27)


## Todo
 - Clean up code
 - Error handling
 - SAM deploy
 - Improve ChatCompletion rules