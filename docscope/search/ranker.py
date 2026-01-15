"""Search result ranking and scoring"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math

from whoosh.scoring import (
    BM25F, TF_IDF, Frequency, MultiWeighting,
    FunctionWeighting
)
from whoosh.searching import Hit

from ..core.logging import get_logger

logger = get_logger(__name__)


class SearchRanker:
    """Custom ranking and scoring for search results"""
    
    def __init__(self, scoring_algorithm: str = "BM25F"):
        """Initialize search ranker
        
        Args:
            scoring_algorithm: Scoring algorithm to use (BM25F, TF_IDF, etc.)
        """
        self.scoring_algorithm = scoring_algorithm
        self.scorer = self._get_scorer()
        
        # Boost factors
        self.boost_factors = {
            'title_match': 2.0,
            'exact_match': 3.0,
            'recent_document': 1.5,
            'popular_document': 1.2,
            'format_preference': 1.1,
        }
    
    def _get_scorer(self):
        """Get the appropriate scoring function
        
        Returns:
            Whoosh scoring function
        """
        if self.scoring_algorithm == "BM25F":
            return BM25F(
                B=0.75,  # Length normalization
                K1=1.2,  # Term frequency saturation
                title_B=0.6,  # Less length norm for titles
            )
        elif self.scoring_algorithm == "TF_IDF":
            return TF_IDF()
        elif self.scoring_algorithm == "Frequency":
            return Frequency()
        else:
            # Default to BM25F
            return BM25F()
    
    def rank_results(
        self,
        results: List[Hit],
        query_string: str,
        user_preferences: Optional[Dict] = None
    ) -> List[Hit]:
        """Rank and re-score search results
        
        Args:
            results: Initial search results
            query_string: Original query string
            user_preferences: User preferences for ranking
            
        Returns:
            Re-ranked results
        """
        if not results:
            return results
        
        # Calculate custom scores
        scored_results = []
        for hit in results:
            custom_score = self._calculate_custom_score(
                hit, query_string, user_preferences
            )
            # Combine with original score
            final_score = hit.score * custom_score
            scored_results.append((final_score, hit))
        
        # Sort by final score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return just the hits
        return [hit for _, hit in scored_results]
    
    def _calculate_custom_score(
        self,
        hit: Hit,
        query_string: str,
        user_preferences: Optional[Dict]
    ) -> float:
        """Calculate custom score for a hit
        
        Args:
            hit: Search result hit
            query_string: Original query
            user_preferences: User preferences
            
        Returns:
            Custom score multiplier
        """
        score = 1.0
        
        # Title match boost
        if self._is_title_match(hit, query_string):
            score *= self.boost_factors['title_match']
        
        # Exact match boost
        if self._is_exact_match(hit, query_string):
            score *= self.boost_factors['exact_match']
        
        # Recency boost
        recency_boost = self._calculate_recency_boost(hit)
        score *= recency_boost
        
        # Format preference
        if user_preferences:
            format_boost = self._calculate_format_boost(hit, user_preferences)
            score *= format_boost
        
        # Popularity (based on access frequency, if available)
        popularity_boost = self._calculate_popularity_boost(hit)
        score *= popularity_boost
        
        return score
    
    def _is_title_match(self, hit: Hit, query_string: str) -> bool:
        """Check if query matches document title
        
        Args:
            hit: Search hit
            query_string: Query string
            
        Returns:
            True if title contains query terms
        """
        title = hit.get('title', '').lower()
        query_terms = query_string.lower().split()
        
        return any(term in title for term in query_terms)
    
    def _is_exact_match(self, hit: Hit, query_string: str) -> bool:
        """Check if document contains exact query phrase
        
        Args:
            hit: Search hit
            query_string: Query string
            
        Returns:
            True if exact match found
        """
        # Remove quotes and special characters
        clean_query = query_string.strip('"').lower()
        
        title = hit.get('title', '').lower()
        if clean_query in title:
            return True
        
        # Check in snippet or content preview
        snippet = hit.get('snippet', '').lower()
        if clean_query in snippet:
            return True
        
        return False
    
    def _calculate_recency_boost(self, hit: Hit) -> float:
        """Calculate boost based on document recency
        
        Args:
            hit: Search hit
            
        Returns:
            Recency boost factor
        """
        modified_at = hit.get('modified_at')
        if not modified_at:
            return 1.0
        
        if isinstance(modified_at, str):
            try:
                modified_at = datetime.fromisoformat(modified_at)
            except:
                return 1.0
        
        # Calculate age in days
        age_days = (datetime.now() - modified_at).days
        
        if age_days < 7:
            return self.boost_factors['recent_document']
        elif age_days < 30:
            return 1.3
        elif age_days < 90:
            return 1.1
        elif age_days > 365:
            return 0.9
        
        return 1.0
    
    def _calculate_format_boost(
        self,
        hit: Hit,
        user_preferences: Dict
    ) -> float:
        """Calculate boost based on format preference
        
        Args:
            hit: Search hit
            user_preferences: User preferences
            
        Returns:
            Format boost factor
        """
        preferred_formats = user_preferences.get('preferred_formats', [])
        if not preferred_formats:
            return 1.0
        
        doc_format = hit.get('format', '')
        if doc_format in preferred_formats:
            return self.boost_factors['format_preference']
        
        return 1.0
    
    def _calculate_popularity_boost(self, hit: Hit) -> float:
        """Calculate boost based on document popularity
        
        Args:
            hit: Search hit
            
        Returns:
            Popularity boost factor
        """
        # This could be based on view count, bookmark count, etc.
        # For now, use a simple score field if available
        score = hit.get('score', 0.0)
        
        if score > 0.8:
            return self.boost_factors['popular_document']
        elif score > 0.5:
            return 1.1
        
        return 1.0
    
    def calculate_relevance_feedback(
        self,
        results: List[Hit],
        clicked_items: List[str],
        ignored_items: List[str]
    ) -> Dict[str, float]:
        """Calculate relevance feedback for improving future searches
        
        Args:
            results: Search results
            clicked_items: IDs of clicked/viewed items
            ignored_items: IDs of ignored items
            
        Returns:
            Feedback scores by document ID
        """
        feedback = {}
        
        for i, hit in enumerate(results):
            doc_id = hit.get('id')
            
            # Position in results (higher = worse)
            position_penalty = math.log(i + 2) / math.log(2)
            
            if doc_id in clicked_items:
                # Positive feedback - clicked despite position
                feedback[doc_id] = 1.0 / position_penalty
            elif doc_id in ignored_items:
                # Negative feedback - ignored despite high position
                feedback[doc_id] = -position_penalty
            else:
                # Neutral
                feedback[doc_id] = 0.0
        
        return feedback
    
    def get_scoring_explanation(self, hit: Hit) -> Dict[str, Any]:
        """Get explanation of scoring for a hit
        
        Args:
            hit: Search hit
            
        Returns:
            Dictionary explaining score components
        """
        explanation = {
            'base_score': hit.score,
            'factors': {}
        }
        
        # Add factor explanations
        if hasattr(hit, 'matched_terms'):
            explanation['matched_terms'] = list(hit.matched_terms())
        
        # Add field matches
        field_matches = {}
        for field in ['title', 'content', 'tags']:
            if hasattr(hit, field):
                field_matches[field] = True
        explanation['field_matches'] = field_matches
        
        return explanation