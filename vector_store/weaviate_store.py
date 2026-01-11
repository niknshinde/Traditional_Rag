# Weaviate Vector Store
# =====================
# This file handles storing and retrieving embeddings from Weaviate

from typing import List, Dict, Any, Optional
import time
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery

from config.settings import config


class WeaviateStore:
    """
    Service for storing and searching documents in Weaviate.
    
    WHAT IS WEAVIATE?
    Weaviate is a vector database - it's designed to store embeddings
    and find similar ones quickly.
    
    Regular databases: "Find all users named John"
    Vector databases: "Find documents similar to this embedding"
    
    HOW DOES IT WORK?
    1. You store documents with their embeddings
    2. When you search, you give it an embedding
    3. It finds the closest embeddings using cosine similarity
    4. Returns the associated documents
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        grpc_port: int = None,
        max_retries: int = 5
    ):
        """
        Initialize connection to Weaviate.
        
        Args:
            host: Weaviate hostname (default: localhost)
            port: HTTP port (default: 8080)
            grpc_port: gRPC port for faster queries (default: 50051)
            max_retries: Max connection attempts (for startup delays)
        """
        self.host = host or config.weaviate.host
        self.port = port or config.weaviate.port
        self.grpc_port = grpc_port or config.weaviate.grpc_port
        self.class_name = config.weaviate.class_name
        self.max_retries = max_retries
        
        # ============================================
        # CONNECTING TO WEAVIATE
        # ============================================
        # We use the v4 client which is more modern and faster
        
        self.client = weaviate.connect_to_local(
            host=self.host,
            port=self.port,
            grpc_port=self.grpc_port
        )
        
        # Create the collection with retry logic
        self._create_collection_with_retry()
    
    def _create_collection_with_retry(self):
        """
        Create collection with retry logic for startup delays.
        
        PYTHON CONCEPT: Exponential Backoff
        ====================================
        When a service is starting up, we don't want to hammer it
        with requests. Instead, we wait longer between each retry:
        - Try 1: wait 2 seconds
        - Try 2: wait 4 seconds
        - Try 3: wait 8 seconds
        - etc.
        
        This is called "exponential backoff" and is a best practice
        for handling temporary failures.
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self._create_collection()
                return  # Success!
            except Exception as e:
                last_error = e
                wait_time = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
                print(f"⏳ Weaviate not ready (attempt {attempt + 1}/{self.max_retries}). Waiting {wait_time}s...")
                time.sleep(wait_time)
        
        # All retries failed
        raise ConnectionError(
            f"Could not connect to Weaviate after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
    
    def _create_collection(self):
        """
        Create the document collection in Weaviate.
        
        WHAT IS A COLLECTION?
        Think of it like a table in a regular database.
        Each collection has:
        - A name (like "Document")
        - Properties (like "content", "source")
        - A vectorizer (how to create embeddings)
        
        We're using "none" vectorizer because we create
        embeddings ourselves with Gemini!
        """
        # ============================================
        # PYTHON CONCEPT: Private Methods (_name)
        # ============================================
        # Methods starting with _ are "private" by convention.
        # It means: "This is for internal use, don't call it directly"
        # Python doesn't enforce this, but it's a signal to other devs.
        
        # Check if collection already exists
        if self.client.collections.exists(self.class_name):
            return  # Already exists, nothing to do
        
        # Create the collection
        self.client.collections.create(
            name=self.class_name,
            # We handle vectors ourselves (Gemini), so no auto-vectorizer
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(
                    name="content",
                    data_type=DataType.TEXT,
                    description="The chunk text content"
                ),
                Property(
                    name="source",
                    data_type=DataType.TEXT,
                    description="Source file path"
                ),
                Property(
                    name="chunk_index",
                    data_type=DataType.INT,
                    description="Index of chunk in original document"
                ),
            ]
        )
        
        print(f"✅ Created collection: {self.class_name}")
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Add documents with their embeddings to Weaviate.
        
        Args:
            texts: List of text chunks
            embeddings: List of embedding vectors (one per text)
            metadata: Optional list of metadata dicts
            
        Returns:
            List of document IDs
        """
        # ============================================
        # VALIDATION
        # ============================================
        # Always check inputs match up!
        if len(texts) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(texts)} texts but {len(embeddings)} embeddings"
            )
        
        collection = self.client.collections.get(self.class_name)
        ids = []
        
        # ============================================
        # PYTHON CONCEPT: zip()
        # ============================================
        # zip() combines multiple lists into tuples
        # 
        # texts = ["a", "b"]
        # embeddings = [[0.1], [0.2]]
        # zip(texts, embeddings) → [("a", [0.1]), ("b", [0.2])]
        #
        # enumerate() adds an index: (0, item), (1, item), ...
        
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            # Get metadata for this item, or empty dict
            meta = metadata[i] if metadata else {}
            
            # Insert into Weaviate
            uuid = collection.data.insert(
                properties={
                    "content": text,
                    "source": meta.get("source", "unknown"),
                    "chunk_index": meta.get("chunk_index", i),
                },
                vector=embedding
            )
            
            ids.append(str(uuid))
        
        print(f"✅ Added {len(ids)} documents to Weaviate")
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using semantic search.
        
        THIS IS THE MAGIC!
        Given a query embedding, Weaviate finds the most similar
        document embeddings using cosine similarity.
        
        Args:
            query_embedding: The embedding of the search query
            top_k: How many results to return
            
        Returns:
            List of matching documents with their content and scores
        """
        collection = self.client.collections.get(self.class_name)
        
        # ============================================
        # THE SEARCH QUERY
        # ============================================
        # near_vector: Find vectors close to this one
        # limit: How many to return
        # return_metadata: Include the distance/similarity score
        
        results = collection.query.near_vector(
            near_vector=query_embedding,
            limit=top_k,
            return_metadata=MetadataQuery(distance=True)
        )
        
        # ============================================
        # FORMATTING RESULTS
        # ============================================
        # We convert Weaviate's response to a simple dict format
        
        formatted_results = []
        for obj in results.objects:
            formatted_results.append({
                "content": obj.properties["content"],
                "source": obj.properties["source"],
                "chunk_index": obj.properties["chunk_index"],
                # Distance is opposite of similarity
                # Lower distance = more similar
                "score": 1 - obj.metadata.distance
            })
        
        return formatted_results
    
    def delete_collection(self):
        """Delete the entire collection (use carefully!)."""
        if self.client.collections.exists(self.class_name):
            self.client.collections.delete(self.class_name)
            print(f"🗑️ Deleted collection: {self.class_name}")
    
    def close(self):
        """Close the Weaviate connection."""
        self.client.close()


# ============================================
# QUICK TEST
# ============================================
if __name__ == "__main__":
    # Make sure Weaviate is running first!
    # docker compose up -d
    
    store = WeaviateStore()
    
    # Add some test documents
    texts = ["Hello world", "Goodbye world"]
    # Fake embeddings (in real use, these come from Gemini)
    fake_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    
    try:
        store.add_documents(texts, fake_embeddings)
        print("Added test documents!")
        
        # Search
        results = store.search(fake_embeddings[0], top_k=2)
        print(f"Search results: {results}")
    finally:
        store.close()
