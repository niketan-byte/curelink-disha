"""
Protocol Matcher Service - Match user queries to health protocols
"""
import logging
import re
from typing import List, Optional

from app.database import get_protocols_collection
from app.models.protocol import Protocol, ProtocolCategory

logger = logging.getLogger(__name__)


class ProtocolMatcher:
    """
    Protocol matching service using keyword-based matching.
    Matches user queries to relevant health protocols.
    """
    
    def __init__(self):
        self.collection = get_protocols_collection()
        self._protocols_cache: Optional[List[Protocol]] = None
    
    async def _load_protocols(self) -> List[Protocol]:
        """Load all active protocols from database."""
        if self._protocols_cache is not None:
            return self._protocols_cache
        
        cursor = self.collection.find({"active": True}).sort("priority", 1)
        
        protocols = []
        async for doc in cursor:
            protocols.append(Protocol.from_dict(doc))
        
        self._protocols_cache = protocols
        logger.info(f"Loaded {len(protocols)} protocols")
        
        return protocols
    
    def invalidate_cache(self) -> None:
        """Invalidate the protocols cache."""
        self._protocols_cache = None
    
    async def match_protocols(
        self,
        query: str,
        category: Optional[ProtocolCategory] = None,
        max_matches: int = 2,
    ) -> List[Protocol]:
        """
        Match a user query to relevant protocols.
        
        Args:
            query: User's message/query
            category: Optional category to filter
            max_matches: Maximum protocols to return
            
        Returns:
            List of matched Protocol objects
        """
        protocols = await self._load_protocols()
        
        # Normalize query
        query_lower = query.lower().strip()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        # Score each protocol
        scored = []
        
        for protocol in protocols:
            # Skip if category filter doesn't match
            if category and protocol.category != category:
                continue
            
            score = self._calculate_match_score(query_words, protocol)
            
            if score > 0:
                scored.append((score, protocol))
        
        # Sort by score (descending) and priority (ascending)
        scored.sort(key=lambda x: (-x[0], x[1].priority))
        
        # Return top matches
        matches = [protocol for _, protocol in scored[:max_matches]]
        
        if matches:
            logger.info(f"Matched {len(matches)} protocols for query: {query[:50]}...")
        
        return matches
    
    def _calculate_match_score(self, query_words: set, protocol: Protocol) -> float:
        """
        Calculate match score between query words and protocol keywords.
        
        Args:
            query_words: Set of words from user query
            protocol: Protocol to score
            
        Returns:
            Match score (0 = no match)
        """
        all_keywords = protocol.get_all_keywords()
        
        if not all_keywords:
            return 0.0
        
        # Count matching keywords
        matches = 0
        keyword_set = set(k.lower() for k in all_keywords)
        
        for query_word in query_words:
            # Exact match
            if query_word in keyword_set:
                matches += 2
            # Partial match (keyword contains query word or vice versa)
            else:
                for keyword in keyword_set:
                    if query_word in keyword or keyword in query_word:
                        matches += 1
                        break
        
        # Normalize by number of keywords
        return matches / len(all_keywords) if matches > 0 else 0.0
    
    async def get_protocols_context(
        self,
        query: str,
        max_protocols: int = 2,
    ) -> str:
        """
        Get formatted protocol context string for LLM.
        
        Args:
            query: User's query
            max_protocols: Maximum protocols to include
            
        Returns:
            Formatted string of matched protocols
        """
        protocols = await self.match_protocols(query, max_matches=max_protocols)
        
        if not protocols:
            return ""
        
        parts = ["## Relevant Health Guidelines\n"]
        
        for protocol in protocols:
            parts.append(protocol.to_context_string())
            parts.append("")  # Empty line between protocols
        
        return "\n".join(parts)
    
    async def get_protocol_by_name(self, name: str) -> Optional[Protocol]:
        """Get a specific protocol by name."""
        doc = await self.collection.find_one({"name": name, "active": True})
        
        if doc:
            return Protocol.from_dict(doc)
        
        return None
    
    async def get_all_protocols(self) -> List[Protocol]:
        """Get all active protocols."""
        return await self._load_protocols()
