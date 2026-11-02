# ADR 0001: Split compute between Lambda and Hugging Face endpoints

Date: 2026-11-02. Base commit: 39ceb36.

Context: BGE embedding, cross-encoder reranking and Mistral-7B generation need GPU memory. Lambda has no GPU and a 250 MB unzipped package limit.

Decision: Run the three models on Hugging Face Inference Endpoints. Lambda only validates the request, calls the endpoints and Pinecone, and shapes the JSON response.

Trade-offs: Each request makes three network calls. Endpoint cold starts can exceed the 30 second HTTP API limit. The package stays small and holds no model weights.
