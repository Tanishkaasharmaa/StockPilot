import os
import glob
from embeddings import OllamaEmbeddingFunction
import pypdf
import email
from email import policy
from simple_store import SimpleVectorStore
import ollama

DATA_DIR = 'd:/Hugo/Data'

def parse_eml(file_path):
    with open(file_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
        
    subject = msg['subject']
    sender = msg['from']
    date = msg['date']
    
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body += part.get_content()
    else:
        body = msg.get_content()
        
    # Create a nice text representation
    text_content = f"Email from {sender} on {date}\nSubject: {subject}\n\n{body}"
    return text_content

def parse_pdf(file_path):
    reader = pypdf.PdfReader(file_path)
    text_content = ""
    for page in reader.pages:
        text_content += page.extract_text() + "\n"
    return text_content

def ingest_data():
    print("Starting document ingestion with Ollama embeddings...")
    
    # Initialize the vector store
    db = SimpleVectorStore()
    db.reset()  # Clear old Gemini embeddings
    
    # Get embedding model from env
    embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    
    all_texts = []
    all_metadatas = []
    
    # Process Emails
    email_dir = os.path.join(DATA_DIR, 'emails')
    if os.path.exists(email_dir):
        for eml_file in glob.glob(os.path.join(email_dir, '*.eml')):
            try:
                text = parse_eml(eml_file)
                all_texts.append(text)
                all_metadatas.append({
                    'source': os.path.basename(eml_file),
                    'type': 'email'
                })
                print(f"Parsed email: {os.path.basename(eml_file)}")
            except Exception as e:
                print(f"Error parsing {eml_file}: {e}")
    
    # Process PDFs (Specs)
    specs_dir = os.path.join(DATA_DIR, 'specs')
    if os.path.exists(specs_dir):
        for pdf_file in glob.glob(os.path.join(specs_dir, '*.pdf')):
            try:
                text = parse_pdf(pdf_file)
                all_texts.append(text)
                all_metadatas.append({
                    'source': os.path.basename(pdf_file),
                    'type': 'specification'
                })
                print(f"Parsed PDF: {os.path.basename(pdf_file)}")
            except Exception as e:
                print(f"Error parsing {pdf_file}: {e}")
    
    # Generate embeddings using Ollama
    print(f"\nGenerating embeddings using {embed_model}...")
    all_embeddings = []
    for i, text in enumerate(all_texts):
        try:
            response = ollama.embeddings(model=embed_model, prompt=text)
            all_embeddings.append(response["embedding"])
            print(f"Generated embedding {i+1}/{len(all_texts)}")
        except Exception as e:
            print(f"Error generating embedding for doc {i}: {e}")
            continue
    
    # Add to vector store
    if all_embeddings:
        db.add(all_texts, all_embeddings, all_metadatas)
        print(f"\n✅ Ingestion complete! Stored {len(all_embeddings)} documents.")
    else:
        print("\n❌ No documents were ingested.")

if __name__ == "__main__":
    ingest_data()
