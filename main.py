"""
RAG Application - Main Entry Point
===================================

This is where you run the application from!

USAGE:
    # Ingest documents
    python main.py ingest path/to/your/file.pdf
    python main.py ingest path/to/folder/

    # Query the system
    python main.py query "What is machine learning?"
    
    # Interactive mode
    python main.py interactive
"""

import sys
import os
from pathlib import Path

# ============================================
# PYTHON CONCEPT: Load environment variables
# ============================================
# dotenv loads variables from .env file into os.environ
# This keeps your API keys out of your code!

from dotenv import load_dotenv
load_dotenv()  # Load .env file

from rag import RAGPipeline


def ingest_command(path: str):
    """
    Ingest a file or all files in a directory.
    
    Args:
        path: Path to a file or directory
    """
    rag = RAGPipeline()
    
    try:
        path_obj = Path(path)
        
        if path_obj.is_file():
            # Single file
            chunks = rag.ingest_document(str(path_obj))
            print(f"\n✅ Done! Ingested {chunks} chunks from {path}")
            
        elif path_obj.is_dir():
            # Directory - find all supported files
            # ============================================
            # PYTHON CONCEPT: glob
            # ============================================
            # glob finds files matching a pattern
            # **/*.pdf means "any .pdf file in any subdirectory"
            
            files = []
            for ext in ['*.pdf', '*.docx', '*.txt']:
                files.extend(path_obj.glob(f'**/{ext}'))
            
            if not files:
                print(f"No PDF, DOCX, or TXT files found in {path}")
                return
            
            print(f"Found {len(files)} files to ingest:")
            for f in files:
                print(f"  - {f}")
            
            total = rag.ingest_multiple([str(f) for f in files])
            print(f"\n✅ Done! Ingested {total} total chunks from {len(files)} files")
        else:
            print(f"❌ Path not found: {path}")
            
    finally:
        rag.close()


def query_command(question: str):
    """
    Answer a question using the RAG system.
    
    Args:
        question: The user's question
    """
    rag = RAGPipeline()
    
    try:
        answer = rag.query(question)
        print("\n" + "=" * 60)
        print("ANSWER:")
        print("=" * 60)
        print(answer)
        
    finally:
        rag.close()


def interactive_command():
    """
    Run an interactive Q&A session.
    
    Type your questions and get answers.
    Type 'quit' or 'exit' to stop.
    """
    print("=" * 60)
    print("🤖 RAG Interactive Mode")
    print("=" * 60)
    print("Ask questions about your ingested documents.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    rag = RAGPipeline()
    
    try:
        while True:
            # ============================================
            # PYTHON CONCEPT: input()
            # ============================================
            # input() reads text from the user
            # The string passed is the "prompt" shown before input
            
            question = input("\n📝 Your question: ").strip()
            
            # Check for exit commands
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            # Skip empty questions
            if not question:
                print("Please enter a question.")
                continue
            
            # Get and display answer
            answer = rag.query(question)
            print("\n" + "-" * 60)
            print("🤖 Answer:")
            print("-" * 60)
            print(answer)
            
    finally:
        rag.close()


def print_usage():
    """Print usage instructions."""
    print("""
RAG Application - Usage
=======================

Commands:

  python main.py ingest <path>
      Ingest a document or folder of documents.
      Supported formats: PDF, DOCX, TXT
      
      Examples:
          python main.py ingest document.pdf
          python main.py ingest ./documents/

  python main.py query "<question>"
      Ask a single question and get an answer.
      
      Example:
          python main.py query "What is the main topic?"

  python main.py interactive
      Start an interactive Q&A session.

Before using:
  1. Make sure Docker is running
  2. Start Weaviate: docker compose up -d
  3. Set your GEMINI_API_KEY in .env file
""")


# ============================================
# PYTHON CONCEPT: if __name__ == "__main__"
# ============================================
# This block only runs when you execute main.py directly:
#   python main.py
#
# It does NOT run if you import from main.py:
#   from main import ingest_command  # This won't trigger the block

if __name__ == "__main__":
    # ============================================
    # PYTHON CONCEPT: sys.argv
    # ============================================
    # sys.argv is a list of command-line arguments
    # 
    # Example: python main.py ingest file.pdf
    # sys.argv = ["main.py", "ingest", "file.pdf"]
    #           [0]         [1]       [2]
    
    # Check if any command was provided
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Route to the appropriate function based on command
    # ============================================
    # PYTHON CONCEPT: match statement
    # ============================================
    
    match command:
        case "ingest":
            if len(sys.argv) < 3:
                print("Error: Please provide a path to ingest")
                print("  Example: python main.py ingest document.pdf")
                sys.exit(1)
            ingest_command(sys.argv[2])
            
        case "query":
            if len(sys.argv) < 3:
                print("Error: Please provide a question")
                print('  Example: python main.py query "What is this about?"')
                sys.exit(1)
            # Join all arguments after "query" as the question
            # This allows questions without quotes
            question = " ".join(sys.argv[2:])
            query_command(question)
            
        case "interactive":
            interactive_command()
            
        case _:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)
