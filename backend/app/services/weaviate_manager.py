class WeaviateManager:
    # ... existing code ...

    def get_chunks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        result = (
            self.client.query
            .get("Chunk", ["content", "source", "start_index", "end_index"])
            .with_additional(["id", "score"])
            .with_near_text({"concepts": [query]})
            .with_limit(limit)
            .do()
        )

        chunks = result["data"]["Get"]["Chunk"]
        return [
            {
                "id": chunk["_additional"]["id"],
                "content": chunk["content"],
                "source": chunk["source"],
                "start_index": chunk["start_index"],
                "end_index": chunk["end_index"],
                "score": chunk["_additional"]["score"],
            }
            for chunk in chunks
        ]