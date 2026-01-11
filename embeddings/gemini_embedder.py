# Gemini Embedding Service
# =========================
# This file handles creating embeddings using Google's Gemini API

from typing import List
from google import genai

from config import config

# ============================================
# PYTHON CONCEPT: Classes
# ============================================
# A class is a blueprint for creating objects.
# 
# Why use a class here instead of functions?
# 1. We can store the API client once (in __init__)
# 2. We don't have to pass the client to every function
# 3. We can add state (like caching) later


class GeminiEmbedder:
    """
    Service for creating text embeddings using Google Gemini.
    
    WHAT IS THIS CLASS DOING?
    1. Takes text as input
    2. Sends it to Google's Gemini API
    3. Gets back a vector (list of numbers) that represents the text
    
    Usage:
        embedder = GeminiEmbedder(api_key="your-key")
        vector = embedder.embed("Hello world")
        # vector is now something like [0.1, -0.3, 0.7, ...]
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the embedder with an API key.
        
        Args:
            api_key: Google API key. If None, uses config.
        """
        # ============================================
        # PYTHON CONCEPT: self
        # ============================================
        # 'self' refers to the instance of the class.
        # When you do: embedder = GeminiEmbedder()
        # 'self' becomes 'embedder'
        #
        # self.model_name stores the model for THIS instance
        
        self.api_key = api_key or config.gemini.api_key
        self.model_name = config.gemini.embedding_model
        
        # ============================================
        # NEW SDK: Client-based API
        # ============================================
        # The new google-genai SDK uses a Client object
        # instead of genai.configure()
        self.client = genai.Client(api_key=self.api_key)
    
    def embed(self, text: str) -> List[float]:
        """
        Create an embedding for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            A list of floats (the embedding vector)
        """
        # ============================================
        # THE API CALL (New SDK)
        # ============================================
        # client.models.embed_content() sends our text to Google
        # and returns the embedding in the response
        
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
        )
        
        # The embedding is in result.embeddings[0].values
        return list(result.embeddings[0].values)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Create an embedding for a search query.
        
        For the new SDK, we use the same method.
        (Task types are handled differently in the new API)
        """
        return self.embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts at once.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (one per text)
        """
        # For now, we embed one at a time
        # The new SDK has batch support but this is simpler to understand
        embeddings = [self.embed(text) for text in texts]
        return embeddings


# ============================================
# QUICK TEST
# ============================================
if __name__ == "__main__":
    # This only runs if you execute: python -m embeddings.gemini_embedder
    
    # Make sure you have GEMINI_API_KEY set!
    embedder = GeminiEmbedder()
    
    # Test with a simple text
    test_text = "The quick brown fox jumps over the lazy dog."
    embedding = embedder.embed(test_text)
    
    print(f"Text: {test_text}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
