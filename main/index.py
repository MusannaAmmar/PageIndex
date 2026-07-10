import os
import time
from dotenv import load_dotenv
from pageindex import PageIndexClient

load_dotenv()
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader


# def submit_main():
#     api_key = os.getenv("PAGEINDEX_API_KEY")
#     if not api_key:
#         raise RuntimeError("Set PAGEINDEX_API_KEY first.")

#     pdf_path = input("Enter full PDF path: ").strip().strip('"')
#     path_obj = Path(pdf_path)

#     if not path_obj.exists():
#         raise FileNotFoundError(f"File not found: {pdf_path}")
#     if path_obj.suffix.lower() != ".pdf":
#         raise ValueError("Only .pdf files are allowed.")

#     # Load with PyPDFLoader
#     loader = PyPDFLoader(str(path_obj))
#     _pages = loader.load()

#     client = PageIndexClient(api_key=api_key)
#     result = client.submit_document(str(path_obj))['doc_id']

#     print("Submitted:", path_obj)
#     print("Response:", result)



def main():
    api_key = os.getenv("PAGEINDEX_API_KEY")
    if not api_key:
        raise RuntimeError("Set PAGEINDEX_API_KEY first.")

    client = PageIndexClient(api_key=api_key)

    # ── Step 1: Provide the doc_id from your upload response ──────────────
    # doc_id = input("Enter the doc_id from your upload response (e.g. pi-abc123): ").strip()

    # # ── Step 2: Wait until the document is fully processed ────────────────
    # print("Checking document status...")
    
    # status = client.get_document(doc_id)
    # print(f"  Status: {status}")
    # if status == "completed":
    #     print("✅ Document is ready!\n")
        
    # elif status == "failed":
    #     raise RuntimeError("❌ Document processing failed.")
    
    list_docs=client.list_documents()
    print(f"  Your documents: {list_docs}")
    docs=list_docs.get("documents",[])
    # doc_id=str([doc['id'] for doc in docs] if docs else None)
    doc_id=docs[0]['id']
    print('Document ID to query:', doc_id)

    get_tree=client.get_tree(doc_id,node_summary=True)
    print(f"  Document tree with summaries: {get_tree}")

    # ── Step 3: Ask your question ─────────────────────────────────────────
    query = input("Enter your question about the document: ").strip()

    # ════════════════════════════════════════════════════════════════════════
    # APPROACH A — Chat API (Recommended, full agentic RAG reasoning)
    # ════════════════════════════════════════════════════════════════════════
    print("\n── Chat API Response ──────────────────────────────────────────")
    response = client.chat_completions(
        messages=[{"role": "user", "content": query}],
        doc_id=doc_id
    )
    answer = response["choices"][0]["message"]["content"]
    print(answer)

    # ════════════════════════════════════════════════════════════════════════
    # APPROACH B — Legacy Retrieval API (returns raw retrieved nodes/chunks)
    # ════════════════════════════════════════════════════════════════════════
    print("\n── Legacy Retrieval Response ──────────────────────────────────")

    # Check retrieval readiness specifically
    if not client.is_retrieval_ready(doc_id):
        print("⚠️  Document not yet ready for legacy retrieval. Try again later.")
        return

    # Submit retrieval query
    retrieval = client.submit_query(
        doc_id=doc_id,
        query=query,
        thinking=False      # set True for reasoning trace
    )
    retrieval_id = retrieval["retrieval_id"]
    print(f"Retrieval task submitted. ID: {retrieval_id}")

    # Poll until retrieval completes
    while True:
        result = client.get_retrieval(retrieval_id)
        if result.get("status") == "completed":
            print("\n📄 Retrieved Nodes:")
            for node in result.get("retrieved_nodes", []):
                print(f"\n  Section : {node.get('title', 'N/A')}")
                print(f"  Content : {node.get('content', '')[:300]}...")   # preview
            break
        elif result.get("status") == "failed":
            raise RuntimeError("Retrieval task failed.")
        print("  Waiting for retrieval result...")
        time.sleep(3)

if __name__ == "__main__":
    # submit_main()
    main()
