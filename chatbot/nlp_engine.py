#!/usr/bin/env python3
"""
NLP Engine for Financial Chatbot
Semantic understanding using Sentence-BERT and Chroma vector DB
"""

import logging
import numpy as np
from config import NLP_CONFIG, CHROMA_CONFIG, QUERY_CATEGORIES, COMPANIES

logger = logging.getLogger(__name__)

class NLPEngine:
    """NLP engine for semantic understanding"""
    
    def __init__(self):
        """Initialize NLP engine with embeddings and vector DB"""
        self.model = None
        self.chroma_client = None
        self.collection = None
        self._init_models()
    
    def _init_models(self):
        """Initialize NLP models with graceful degradation"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(NLP_CONFIG['model_name'])
            logger.info(f"Loaded {NLP_CONFIG['model_name']}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback keyword matching")
            self.model = None
        
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=CHROMA_CONFIG['path'])
            self.collection = self.chroma_client.get_or_create_collection(
                name=CHROMA_CONFIG['collection_name'],
                metadata={"hnsw:space": CHROMA_CONFIG['similarity_metric']}
            )
            logger.info("Chroma vector DB initialized")
        except ImportError:
            logger.warning("chromadb not installed, vector search unavailable")
            self.chroma_client = None
    
    def embed_text(self, text):
        """Generate embedding for text"""
        if self.model is None:
            logger.warning("No embedding model available")
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None
    
    def semantic_similarity(self, query, candidates):
        """
        Compute semantic similarity between query and candidates
        Returns ranked list of candidates by similarity
        """
        if self.model is None or not candidates:
            return []
        
        try:
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            similarities = []
            
            for candidate in candidates:
                candidate_embedding = self.model.encode(candidate, convert_to_numpy=True)
                similarity = np.dot(query_embedding, candidate_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(candidate_embedding)
                )
                similarities.append({
                    'candidate': candidate,
                    'similarity': float(similarity)
                })
            
            # Sort by similarity descending
            return sorted(similarities, key=lambda x: x['similarity'], reverse=True)
        
        except Exception as e:
            logger.error(f"Similarity computation error: {e}")
            return []
    
    def classify_query(self, query):
        """
        Classify query into one of 7 categories
        Uses both semantic similarity and keyword matching
        """
        query_lower = query.lower()
        scores = {}
        
        # Keyword matching scoring
        for category, config in QUERY_CATEGORIES.items():
            score = 0
            for keyword in config['keywords']:
                if keyword in query_lower:
                    score += 1
            scores[category] = score
        
        # Try semantic matching if model available
        if self.model is not None:
            try:
                category_examples = {
                    'revenue': 'What is the total revenue and sales figures?',
                    'profitability': 'How profitable is the company with margin analysis?',
                    'liquidity': 'What is the operating cash flow and liquidity position?',
                    'leverage': 'What is the debt level and financial risk?',
                    'efficiency': 'How efficient are assets in generating returns?',
                    'trend': 'What are the growth trends and trajectories?',
                    'comparison': 'Compare the financial metrics of companies'
                }
                
                similarities = self.semantic_similarity(query, category_examples.values())
                
                if similarities:
                    # Get top 2 similar categories
                    for i, sim in enumerate(similarities[:2]):
                        for cat, example in category_examples.items():
                            if example == sim['candidate']:
                                if cat not in scores:
                                    scores[cat] = 0
                                scores[cat] += (2 - i) * sim['similarity']
            
            except Exception as e:
                logger.warning(f"Semantic classification failed: {e}")
        
        # Return category with highest score, default to 'comparison'
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'general'
    
    def extract_entities(self, query):
        """
        Extract entities from query:
        - Companies mentioned
        - Metrics interested in
        - Time periods
        """
        query_lower = query.lower()
        entities = {
            'companies': [],
            'metrics': [],
            'time_period': None
        }
        
        # Company extraction
        for company in COMPANIES:
            if company.lower() in query_lower:
                entities['companies'].append(company)
        
        # Metric extraction
        metric_keywords = {
            'revenue': ['revenue', 'sales', 'turnover'],
            'net_income': ['net income', 'earnings', 'profit'],
            'assets': ['assets', 'balance sheet'],
            'liabilities': ['liabilities', 'debt', 'obligations'],
            'cash_flow': ['cash flow', 'ocf', 'operating cash'],
            'margin': ['margin', 'profit margin'],
            'roa': ['roa', 'return on assets']
        }
        
        for metric, keywords in metric_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    entities['metrics'].append(metric)
                    break
        
        # Time period extraction
        time_keywords = {
            'latest': ['latest', 'recent', 'current', 'now', '2024', 'today'],
            'trend': ['trend', 'growth', 'over time', 'yoy', 'year over year'],
            'historical': ['historical', 'past', 'previous', 'history']
        }
        
        for period, keywords in time_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    entities['time_period'] = period
                    break
        
        # Remove duplicates
        entities['companies'] = list(set(entities['companies']))
        entities['metrics'] = list(set(entities['metrics']))
        
        return entities
    
    def search_vector_db(self, query, n_results=3):
        """
        Search vector database for similar documents
        Returns top-n similar financial documents
        """
        if self.collection is None:
            return []
        
        try:
            query_embedding = self.embed_text(query)
            
            if query_embedding is None:
                return []
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Vector DB search error: {e}")
            return []
    
    def add_documents_to_vector_db(self, documents, metadatas=None):
        """
        Add documents to vector database
        documents: list of text strings
        metadatas: list of metadata dicts
        """
        if self.collection is None:
            logger.warning("Vector DB not available")
            return
        
        try:
            embeddings = []
            for doc in documents:
                embedding = self.embed_text(doc)
                if embedding:
                    embeddings.append(embedding)
            
            if embeddings:
                ids = [f"doc_{i}" for i in range(len(documents))]
                
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas or [{} for _ in documents]
                )
                
                logger.info(f"Added {len(documents)} documents to vector DB")
        
        except Exception as e:
            logger.error(f"Error adding documents to vector DB: {e}")

if __name__ == '__main__':
    # Test NLP engine
    nlp = NLPEngine()
    
    # Test classification
    test_queries = [
        "What is Microsoft's revenue?",
        "Compare Apple and Microsoft profitability",
        "Show me the debt levels",
        "What about the cash flow?"
    ]
    
    print("Query Classification Test:")
    for query in test_queries:
        category = nlp.classify_query(query)
        entities = nlp.extract_entities(query)
        print(f"\nQ: {query}")
        print(f"Category: {category}")
        print(f"Entities: {entities}")
