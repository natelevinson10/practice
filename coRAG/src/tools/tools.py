import requests
import json
from dotenv import load_dotenv
import os
load_dotenv()


def rag_search(query: str):
    """Execute a RAG search using Vectara API"""
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

    for _ in obj["search_results"]:
        chunks.append(_["text"])
    
    return chunks

# OpenAI function schema for the rag_search tool
rag_search_tool_schema = {
    "type": "function",
    "function": {
        "name": "rag_search",
        "description": "Search through a knowledge base using RAG (Retrieval Augmented Generation) to find relevant information about topics like order calculations, status criteria, and business logic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant information in the knowledge base"
                }
            },
            "required": ["query"]
        }
    }
}

# Tool registry for easy access
AVAILABLE_TOOLS = {
    "rag_search": rag_search
}






