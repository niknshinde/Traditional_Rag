# RAG Pipeline
# ============
# This is the main orchestrator that ties everything together

from typing import List, Dict, Any
from openai import OpenAI

from config.settings import config
from document_processing import load_document, chunk_text
from embeddings import GeminiEmbedder
from vector_store import WeaviateStore


class RAGPipeline:
    """
    The main RAG (Retrieval-Augmented Generation) pipeline.
    
    THIS CLASS ORCHESTRATES THE ENTIRE FLOW:
    
    INGESTION (storing documents):
        Document → Chunks → Embeddings → Vector DB
    
    QUERY (answering questions):
        Question → Embedding → Search → Context → LLM → Answer
    
    """
    
    def __init__(self):
        """Initialize all components of the RAG pipeline."""
        # ============================================
        # PYTHON CONCEPT: Composition
        # ============================================
        # Instead of doing everything in one class, we CREATE
        # instances of specialized classes. This is called "composition".
        # 
        # Benefits:
        # 1. Each class has one job (Single Responsibility)
        # 2. Easy to swap implementations (e.g., different vector DB)
        # 3. Easier to test each piece separately
        
        self.embedder = GeminiEmbedder()
        self.vector_store = WeaviateStore()
        self.chunk_size = config.chunk.chunk_size
        self.chunk_overlap = config.chunk.chunk_overlap
        
        # Configure OpenRouter for LLM responses
        # OpenRouter uses OpenAI-compatible API!
        self.llm_client = OpenAI(
            base_url=config.openrouter.base_url,
            api_key=config.openrouter.api_key
        )
        self.llm_model = config.openrouter.model
    
    # ============================================
    # INGESTION PIPELINE
    # ============================================
    
    def ingest_document(self, file_path: str) -> int:
        """
        Ingest a document into the RAG system.
        
        FLOW:
        1. Load the document (PDF/DOCX/TXT)
        2. Split into chunks with overlap
        3. Create embeddings for each chunk
        4. Store in vector database
        
        Args:
            file_path: Path to the document
            
        Returns:
            Number of chunks ingested
        """
        print(f"📄 Loading document: {file_path}")
        
        # Step 1: Load document text
        text = load_document(file_path)
        print(f"   ✓ Loaded {len(text)} characters")
        
        # Step 2: Chunk the text
        chunks = chunk_text(
            text,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        print(f"   ✓ Created {len(chunks)} chunks")
        
        # Step 3: Create embeddings
        print(f"   ⏳ Creating embeddings...")
        embeddings = self.embedder.embed_batch(chunks)
        print(f"   ✓ Created {len(embeddings)} embeddings")
        
        # Step 4: Prepare metadata for each chunk
        # ============================================
        # PYTHON CONCEPT: List Comprehension with enumerate
        # ============================================
        # This creates a list of dicts, one per chunk:
        # [{"source": "file.pdf", "chunk_index": 0}, ...]
        
        metadata = [
            {"source": file_path, "chunk_index": i}
            for i in range(len(chunks))
        ]
        
        # Step 5: Store in vector database
        self.vector_store.add_documents(
            texts=chunks,
            embeddings=embeddings,
            metadata=metadata
        )
        
        print(f"✅ Ingested document: {file_path}")
        return len(chunks)
    
    def ingest_multiple(self, file_paths: List[str]) -> int:
        """
        Ingest multiple documents.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Total number of chunks ingested
        """
        total_chunks = 0
        
        for path in file_paths:
            try:
                chunks = self.ingest_document(path)
                total_chunks += chunks
            except Exception as e:
                # ============================================
                # ERROR HANDLING
                # ============================================
                # Don't let one bad file stop the whole process!
                # Log the error and continue with the next file.
                print(f"❌ Error ingesting {path}: {e}")
                continue
        
        return total_chunks
    
    # ============================================
    # QUERY PIPELINE
    # ============================================
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        FLOW:
        1. Create embedding for the query
        2. Search vector database for similar chunks
        
        Args:
            query: The user's question
            top_k: Number of results to retrieve
            
        Returns:
            List of relevant document chunks with scores
        """
        # Create query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Search for similar documents
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        return results
    
    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generate an answer using the LLM with retrieved context.
        
        THIS IS WHERE THE "GENERATION" HAPPENS!
        We combine the retrieved chunks into a prompt and
        ask the LLM to answer based on that context.
        
        Args:
            query: The user's question
            context_chunks: Retrieved document chunks
            
        Returns:
            The generated answer
        """
        # ============================================
        # PROMPT ENGINEERING
        # ============================================
        # The quality of your prompt significantly affects
        # the quality of the answer!
        #
        # Key elements:
        # 1. System instruction (who is the AI?)
        # 2. Context (the retrieved chunks)
        # 3. The question
        # 4. Constraints (what NOT to do)
        
        # Combine all chunks into one context string
        context_text = "\n\n---\n\n".join([
            f"[Source: {chunk['source']}]\n{chunk['content']}"
            for chunk in context_chunks
        ])
        
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.

CONTEXT:
{context_text}

QUESTION:
{query}

INSTRUCTIONS:
1. Answer based ONLY on the context provided above.
2. If the context doesn't contain enough information, say so.
3. Be concise but thorough.
4. Cite which source(s) you used when relevant.

ANSWER:"""
        
        # Generate the response using OpenRouter (OpenAI-compatible API)
        response = self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    def query(self, question: str, top_k: int = 5) -> str:
        """
        The main query method - combines retrieval and generation.
        
        THIS IS WHAT USERS WILL CALL!
        
        Args:
            question: The user's question
            top_k: Number of chunks to retrieve
            
        Returns:
            The generated answer
        """
        print(f"🔍 Searching for: {question}")
        
        # Step 1: Retrieve relevant chunks
        results = self.retrieve(question, top_k=top_k)
        
        if not results:
            return "I couldn't find any relevant information to answer your question."
        
        print(f"   ✓ Found {len(results)} relevant chunks")
        
        # Step 2: Generate answer
        print(f"   ⏳ Generating answer...")
        answer = self.generate_answer(question, results)
        
        return answer
    
    def close(self):
        """Clean up resources."""
        self.vector_store.close()


# ============================================
# QUICK TEST
# ============================================
if __name__ == "__main__":
    rag = RAGPipeline()
    
    try:
        # Example: Ingest a document
        # rag.ingest_document("path/to/your/document.pdf")
        
        # Example: Query
        # answer = rag.query("What is the main topic of this document?")
        # print(answer)
        
        print("RAG Pipeline initialized successfully!")
        print("Use rag.ingest_document() to add documents")
        print("Use rag.query() to ask questions")
        
    finally:
        rag.close()
