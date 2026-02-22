import os
import sys
import time

# Add the project root to sys.path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.rag.ingestion import ingest_pdf
from backend.config import settings

def main():
    pdf_dir = settings.PDF_DIR
    if not os.path.exists(pdf_dir):
        print(f"Directory {pdf_dir} does not exist.")
        return

    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}.")
        return

    print(f"Found {len(pdf_files)} PDF files. Starting ingestion...")
    
    total_start_time = time.time()
    for i, filename in enumerate(pdf_files):
        file_path = os.path.join(pdf_dir, filename)
        print(f"[{i+1}/{len(pdf_files)}] Ingesting {filename}...", end="", flush=True)
        
        start_time = time.time()
        try:
            records = ingest_pdf(file_path)
            duration = (time.time() - start_time)
            print(f" Done! ({len(records)} chunks, {duration:.2f}s)")
        except Exception as e:
            print(f" Failed! Error: {str(e)}")

    total_duration = time.time() - total_start_time
    print(f"\nIngestion complete. Total time: {total_duration:.2f}s")

if __name__ == "__main__":
    main()
