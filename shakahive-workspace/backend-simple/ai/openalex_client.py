"""
OpenAlex API Client - Comprehensive Research Data Integration
Fetches publications, authors, institutions, and research data for enhanced screening
"""

import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import time


class OpenAlexClient:
    """Client for OpenAlex API - comprehensive research database"""
    
    def __init__(self, email: Optional[str] = None):
        """
        Initialize OpenAlex client
        
        Args:
            email: Optional email for API rate limiting (OpenAlex requires polite usage)
        """
        self.base_url = "https://api.openalex.org"
        self.email = email or "novarai-system@example.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'NOVARAai/1.0 (mailto:{self.email})',
            'Accept': 'application/json'
        })
    
    def search_publications(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for publications matching a query
        
        Args:
            query: Search query (keywords, title, abstract)
            limit: Maximum number of results
            
        Returns:
            List of publication data
        """
        try:
            url = f"{self.base_url}/works"
            params = {
                'search': query,
                'per-page': limit,
                'filter': 'type:article',  # Focus on journal articles
                'sort': 'cited_by_count:desc'  # Most cited first
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            publications = []
            
            for work in data.get('results', []):
                pub = {
                    'id': work.get('id', ''),
                    'title': work.get('title', ''),
                    'publication_year': work.get('publication_year'),
                    'type': work.get('type'),
                    'cited_by_count': work.get('cited_by_count', 0),
                    'authors': [author.get('author', {}).get('display_name', '') 
                              for author in work.get('authorships', [])],
                    'journal': work.get('primary_location', {}).get('source', {}).get('display_name', ''),
                    'concepts': [concept.get('display_name', '') 
                              for concept in work.get('concepts', [])[:5]],
                    'abstract': self._extract_abstract(work),
                    'doi': work.get('doi', ''),
                    'url': work.get('id', '')
                }
                publications.append(pub)
            
            return publications
            
        except Exception as e:
            print(f"Error searching publications: {e}")
            return []
    
    def search_authors(self, name: str, institution: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for authors by name and optionally institution
        
        Args:
            name: Author name
            institution: Optional institution filter
            limit: Maximum number of results
            
        Returns:
            List of author data
        """
        try:
            url = f"{self.base_url}/authors"
            params = {
                'search': name,
                'per-page': limit,
                'sort': 'works_count:desc'
            }
            
            if institution:
                params['filter'] = f'last_known_institution.display_name:{institution}'
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            authors = []
            
            for author in data.get('results', []):
                auth = {
                    'id': author.get('id', ''),
                    'display_name': author.get('display_name', ''),
                    'works_count': author.get('works_count', 0),
                    'cited_by_count': author.get('cited_by_count', 0),
                    'h_index': author.get('h_index', 0),
                    'last_known_institution': author.get('last_known_institution', {}).get('display_name', ''),
                    'concepts': [concept.get('display_name', '') 
                              for concept in author.get('concepts', [])[:5]],
                    'orcid': author.get('orcid', ''),
                    'url': author.get('id', '')
                }
                authors.append(auth)
            
            return authors
            
        except Exception as e:
            print(f"Error searching authors: {e}")
            return []
    
    def search_institutions(self, name: str, country: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for institutions by name and optionally country
        
        Args:
            name: Institution name
            country: Optional country filter
            limit: Maximum number of results
            
        Returns:
            List of institution data
        """
        try:
            url = f"{self.base_url}/institutions"
            params = {
                'search': name,
                'per-page': limit,
                'sort': 'works_count:desc'
            }
            
            if country:
                params['filter'] = f'country_code:{country}'
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            institutions = []
            
            for inst in data.get('results', []):
                institution = {
                    'id': inst.get('id', ''),
                    'display_name': inst.get('display_name', ''),
                    'country_code': inst.get('country_code', ''),
                    'country_name': inst.get('country_name', ''),
                    'type': inst.get('type', ''),
                    'works_count': inst.get('works_count', 0),
                    'cited_by_count': inst.get('cited_by_count', 0),
                    'h_index': inst.get('h_index', 0),
                    'concepts': [concept.get('display_name', '') 
                                for concept in inst.get('concepts', [])[:5]],
                    'url': inst.get('id', '')
                }
                institutions.append(institution)
            
            return institutions
            
        except Exception as e:
            print(f"Error searching institutions: {e}")
            return []
    
    def get_concepts(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Extract research concepts from text using OpenAlex taxonomy
        
        Args:
            text: Text to analyze
            limit: Maximum number of concepts
            
        Returns:
            List of concept data
        """
        try:
            # Extract keywords from text
            words = text.lower().split()
            keywords = [word for word in words if len(word) > 4][:10]
            
            if not keywords:
                return []
            
            # Search for concepts
            url = f"{self.base_url}/concepts"
            params = {
                'search': ' '.join(keywords),
                'per-page': limit,
                'sort': 'works_count:desc'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            concepts = []
            
            for concept in data.get('results', []):
                concept_data = {
                    'id': concept.get('id', ''),
                    'display_name': concept.get('display_name', ''),
                    'level': concept.get('level', 0),
                    'works_count': concept.get('works_count', 0),
                    'description': concept.get('description', ''),
                    'ancestors': [ancestor.get('display_name', '') 
                                for ancestor in concept.get('ancestors', [])]
                }
                concepts.append(concept_data)
            
            return concepts
            
        except Exception as e:
            print(f"Error getting concepts: {e}")
            return []
    
    def check_publication_similarity(self, text: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Check text similarity against OpenAlex publications
        Enhanced plagiarism detection with authoritative sources
        
        Args:
            text: Text to check
            limit: Maximum number of similar publications
            
        Returns:
            List of similar publications with similarity scores
        """
        try:
            # Extract key phrases from text (first 3 sentences)
            sentences = text.split('.')[:3]
            query = ' '.join(sentences[:2])  # Use first 2 sentences as query
            
            publications = self.search_publications(query, limit)
            
            # Calculate similarity scores (simplified - could use more sophisticated NLP)
            similar_pubs = []
            text_lower = text.lower()
            
            for pub in publications:
                pub_text = (pub.get('title', '') + ' ' + pub.get('abstract', '')).lower()
                
                # Simple word overlap similarity
                text_words = set(text_lower.split())
                pub_words = set(pub_text.split())
                
                if len(text_words) > 0 and len(pub_words) > 0:
                    overlap = len(text_words & pub_words)
                    similarity = (overlap / len(text_words)) * 100
                    
                    if similarity > 10:  # Only include if >10% similarity
                        similar_pubs.append({
                            **pub,
                            'similarity_score': round(similarity, 2),
                            'source': 'OpenAlex',
                            'type': 'publication'
                        })
            
            # Sort by similarity score
            similar_pubs.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return similar_pubs[:limit]
            
        except Exception as e:
            print(f"Error checking publication similarity: {e}")
            return []
    
    def verify_institution(self, institution_name: str) -> Dict[str, Any]:
        """
        Verify if an institution exists in OpenAlex
        
        Args:
            institution_name: Name of institution to verify
            
        Returns:
            Verification result with institution data
        """
        try:
            institutions = self.search_institutions(institution_name, limit=5)
            
            if not institutions:
                return {
                    'verified': False,
                    'message': 'Institution not found in OpenAlex database',
                    'suggestions': []
                }
            
            # Check for exact or very close match
            best_match = institutions[0]
            institution_lower = institution_name.lower()
            best_match_lower = best_match['display_name'].lower()
            
            if institution_lower in best_match_lower or best_match_lower in institution_lower:
                return {
                    'verified': True,
                    'institution': best_match,
                    'message': 'Institution verified in OpenAlex'
                }
            else:
                return {
                    'verified': False,
                    'message': 'Close matches found but not exact',
                    'suggestions': [inst['display_name'] for inst in institutions[:3]]
                }
                
        except Exception as e:
            print(f"Error verifying institution: {e}")
            return {
                'verified': False,
                'message': f'Error verifying institution: {str(e)}',
                'suggestions': []
            }
    
    def get_research_field_trends(self, field: str, years: int = 5) -> Dict[str, Any]:
        """
        Get trends and statistics for a research field
        
        Args:
            field: Research field name
            years: Number of years to analyze
            
        Returns:
            Trend data and statistics
        """
        try:
            # Search for publications in the field
            url = f"{self.base_url}/works"
            params = {
                'filter': f'concepts.display_name:{field}',
                'per-page': 20,
                'sort': 'publication_year:desc'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            works = data.get('results', [])
            
            if not works:
                return {
                    'field': field,
                    'found': False,
                    'message': 'No publications found for this field'
                }
            
            # Analyze trends
            years_data = {}
            for work in works:
                year = work.get('publication_year')
                if year:
                    years_data[year] = years_data.get(year, 0) + 1
            
            return {
                'field': field,
                'found': True,
                'total_works': len(works),
                'years_data': years_data,
                'average_citations': sum(w.get('cited_by_count', 0) for w in works) / len(works),
                'top_authors': [w.get('authorships', [{}])[0].get('author', {}).get('display_name', '') 
                               for w in works[:5]]
            }
            
        except Exception as e:
            print(f"Error getting research field trends: {e}")
            return {
                'field': field,
                'found': False,
                'message': f'Error: {str(e)}'
            }
    
    def _extract_abstract(self, work: Dict[str, Any]) -> str:
        """Extract abstract from OpenAlex work data"""
        try:
            inverted_abstract = work.get('abstract_inverted_index')
            if inverted_abstract:
                # Reconstruct abstract from inverted index
                words = [None] * max(pos for positions in inverted_abstract.values() for pos in positions) + 1
                for word, positions in inverted_abstract.items():
                    for pos in positions:
                        words[pos] = word
                return ' '.join(filter(None, words))
            return ""
        except:
            return ""
