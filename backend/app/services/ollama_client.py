"""
Ollama Cloud Client

Handles chat completions and embeddings via Ollama Cloud API.
"""

from typing import List, Dict, Optional, Any, AsyncIterator
import httpx
from loguru import logger

from app.core.config import settings


class OllamaClient:
    """Client for Ollama Cloud API."""
    
    def __init__(self):
        self.base_url = settings.ollama_api_url
        self.api_key = settings.ollama_api_key
        self.chat_model = settings.ollama_chat_model
        self.embed_model = settings.ollama_embed_model
        self.timeout = 60.0
        # Configure SSL verification from settings
        self.verify_ssl = settings.ollama_verify_ssl
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream response
            temperature: Sampling temperature (0-1)
            max_tokens: Max tokens to generate
            
        Returns:
            Response dict with 'message' key
        """
        endpoint = f"{self.base_url}/api/chat"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        logger.debug(f"Ollama Chat: model={self.chat_model}, messages={len(messages)}")
        
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Ollama Chat Success")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Ollama Request Error: {str(e)}")
            raise
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            
        Yields:
            Content chunks as they arrive
        """
        endpoint = f"{self.base_url}/api/chat"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }
        
        logger.debug(f"Ollama Chat Stream: model={self.chat_model}")
        
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                async with client.stream(
                    "POST",
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            import json
                            try:
                                chunk = json.loads(line)
                                if "message" in chunk and "content" in chunk["message"]:
                                    yield chunk["message"]["content"]
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in stream: {line}")
                                continue
                    
                    logger.info("Ollama Chat Stream completed")
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama Stream HTTP Error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Ollama Stream Request Error: {str(e)}")
            raise
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        endpoint = f"{self.base_url}/api/embeddings"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        logger.debug(f"Ollama Embed: model={self.embed_model}, texts={len(texts)}")
        
        embeddings = []
        
        # Process each text individually
        for text in texts:
            payload = {
                "model": self.embed_model,
                "prompt": text,
            }
            
            try:
                async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                    response = await client.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout
                    )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if "embedding" in data:
                        embeddings.append(data["embedding"])
                    else:
                        logger.warning(f"No embedding in response for text: {text[:50]}")
                        embeddings.append([])
                        
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama Embed HTTP Error: {e.response.status_code}")
                embeddings.append([])
            except httpx.RequestError as e:
                logger.error(f"Ollama Embed Request Error: {str(e)}")
                embeddings.append([])
        
        logger.info(f"Ollama Embed Success: {len(embeddings)} embeddings generated")
        return embeddings


# Singleton instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
