import requests
import json
from dotenv import load_dotenv
import os
from agents import function_tool
from rich.console import Console

load_dotenv()
console = Console()


@function_tool
def rag_search(query: str) -> list:
    """
    Search through a knowledge base using RAG (Retrieval Augmented Generation) 
    to find relevant information about topics like order calculations, status criteria, and business logic.
    
    Args:
        query: The search query to find relevant information in the knowledge base
        
    Returns:
        A list of relevant text chunks from the knowledge base
    """
    # Display the query being run
    console.print(f"[bright_black]Running query: {query}[/bright_black]")
    
    url = "https://api.vectara.io/v2/chats"

    headers = {
        "customer-id": "322088514",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("VECTARA_API_KEY")
    }

    data = {
        "query": query,
        "search": {
            "corpora": [
                {
                    "corpus_key": "TPCH_dataset",
                    "metadata_filter": "",
                    "lexical_interpolation": 0.005,
                    "custom_dimensions": {}
                }
            ],
            "offset": 0,
            "limit": 25,
            "context_configuration": {
                "sentences_before": 2,
                "sentences_after": 2,
                "start_tag": "%START_SNIPPET%",
                "end_tag": "%END_SNIPPET%"
            },
            "reranker": {
                "type": "customer_reranker",
                "reranker_id": "rnk_272725719"
            }
        },
        "stream_response": False,
        "generation": {
            "generation_preset_name": "vectara-summary-table-md-query-ext-jan-2025-gpt-4o",
            "max_used_search_results": 5,
            "response_language": "eng",
            "enable_factual_consistency_score": True
        },
        "chat": {
            "store": True
        }
    }

    # Just parse the response body as JSON
    response = requests.post(url, headers=headers, json=data)
    obj = response.json()
    chunks = []

    for result in obj["search_results"]:
        chunks.append(result["text"])
    
    return chunks