# Text Chunker
# ============
# This file handles splitting text into smaller chunks with overlap

from typing import List

# ============================================
# PYTHON CONCEPT: Type Hints
# ============================================
# Type hints don't change how the code runs, but they:
# 1. Help you understand what a function expects/returns
# 2. Let your IDE give better autocomplete
# 3. Let tools like mypy catch bugs before running
#
# Examples:
#   def greet(name: str) -> str:     # takes string, returns string
#   def get_items() -> List[str]:    # returns list of strings


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Split text into overlapping chunks.
    
    WHY OVERLAP?
    Imagine your text is:
        "The Eiffel Tower is in Paris. Paris is the capital of France."
    
    If we split exactly at "Paris." with no overlap:
        Chunk 1: "The Eiffel Tower is in Paris."
        Chunk 2: "Paris is the capital of France."
    
    Now if someone asks "What city is the Eiffel Tower in?", 
    Chunk 1 has the answer. But what if they ask "What country 
    has the Eiffel Tower?" - we need BOTH chunks to answer!
    
    With overlap, Chunk 2 would also contain "...in Paris. Paris is..."
    giving more context.
    
    Args:
        text: The full text to chunk
        chunk_size: Maximum size of each chunk (in characters)
        chunk_overlap: How many characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    # ============================================
    # EDGE CASES - Always handle these first!
    # ============================================
    
    # If text is empty, return empty list
    if not text:
        return []
    
    # If text is smaller than chunk_size, return it as single chunk
    if len(text) <= chunk_size:
        return [text]
    
    # ============================================
    # THE ALGORITHM: Sliding Window
    # ============================================
    # 
    # Think of it like a window sliding over text:
    #
    # Text: [===========================================]
    #       |<-- chunk_size -->|
    #                   |<-- overlap -->|
    #                   |<-- chunk_size -->|
    #
    # Each new chunk starts at: previous_start + chunk_size - overlap
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Calculate end position
        end = start + chunk_size
        
        # Extract the chunk
        chunk = text[start:end]
        
        # ============================================
        # PYTHON CONCEPT: String Slicing
        # ============================================
        # text[start:end] extracts characters from index 'start' to 'end-1'
        # Example: "Hello"[0:3] → "Hel"
        
        chunks.append(chunk)
        
        # Move the window forward (minus overlap)
        start = start + chunk_size - chunk_overlap
        
        # ============================================
        # AVOIDING INFINITE LOOP
        # ============================================
        # If overlap >= chunk_size, we'd never move forward!
        # Example: chunk_size=100, overlap=150
        # start = 0 + 100 - 150 = -50 (goes backward!)
        # We prevent this in validation, but this is why it matters.
    
    return chunks


# ============================================
# BONUS: Smart Chunking (Split on Sentences)
# ============================================
# The above is "character-based" chunking.
# A smarter approach is to split on sentence boundaries.
# We'll implement this later if you want!


if __name__ == "__main__":
    # ============================================
    # PYTHON CONCEPT: __name__ == "__main__"
    # ============================================
    # This code only runs if you execute this file directly:
    #   python chunker.py
    #
    # It does NOT run if you import this file:
    #   from document_processing.chunker import chunk_text
    #
    # This is great for testing!
    
    sample_text = """
    Artificial Intelligence (AI) is transforming every industry.
    Machine learning, a subset of AI, allows computers to learn from data.
    Deep learning uses neural networks with many layers.
    Natural Language Processing (NLP) helps computers understand human language.
    RAG combines retrieval with generation for better AI responses.
    """
    
    chunks = chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
    
    print(f"Original text length: {len(sample_text)}")
    print(f"Number of chunks: {len(chunks)}")
    print("-" * 50)
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1} ({len(chunk)} chars):")
        print(chunk[:50] + "..." if len(chunk) > 50 else chunk)
        print("-" * 50)
