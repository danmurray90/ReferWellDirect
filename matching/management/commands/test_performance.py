"""
Management command to test performance optimizations.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from referrals.models import Referral
from matching.services import MatchingService, VectorEmbeddingService, BM25Service
from matching.routing_service import ReferralRoutingService
import time
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test performance optimizations and caching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-caching',
            action='store_true',
            help='Test caching functionality'
        )
        parser.add_argument(
            '--test-embeddings',
            action='store_true',
            help='Test embedding generation performance'
        )
        parser.add_argument(
            '--test-bm25',
            action='store_true',
            help='Test BM25 search performance'
        )
        parser.add_argument(
            '--test-matching',
            action='store_true',
            help='Test full matching performance'
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear all caches before testing'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing performance optimizations...'))
        
        if options['clear_cache']:
            self.clear_caches()
        
        if options['test_caching']:
            self.test_caching()
        
        if options['test_embeddings']:
            self.test_embeddings()
        
        if options['test_bm25']:
            self.test_bm25()
        
        if options['test_matching']:
            self.test_matching()
        
        if not any([options['test_caching'], options['test_embeddings'], 
                   options['test_bm25'], options['test_matching']]):
            # Run all tests if none specified
            self.test_caching()
            self.test_embeddings()
            self.test_bm25()
            self.test_matching()

    def clear_caches(self):
        """Clear all caches."""
        self.stdout.write('Clearing all caches...')
        routing_service = ReferralRoutingService()
        routing_service.clear_all_caches()
        self.stdout.write(self.style.SUCCESS('Caches cleared'))

    def test_caching(self):
        """Test caching functionality."""
        self.stdout.write('\nTesting caching functionality...')
        self.stdout.write('=' * 50)
        
        # Test embedding caching
        vector_service = VectorEmbeddingService()
        test_text = "Test text for caching performance"
        
        # First call (should be slow - no cache)
        start_time = time.time()
        embedding1 = vector_service.generate_embedding(test_text)
        first_call_time = time.time() - start_time
        
        # Second call (should be fast - from cache)
        start_time = time.time()
        embedding2 = vector_service.generate_embedding(test_text)
        second_call_time = time.time() - start_time
        
        self.stdout.write(f"First embedding call: {first_call_time:.4f}s")
        self.stdout.write(f"Second embedding call: {second_call_time:.4f}s")
        self.stdout.write(f"Speed improvement: {first_call_time/second_call_time:.2f}x")
        
        # Test BM25 caching
        bm25_service = BM25Service()
        # Build a small index for testing
        from catalogue.models import Psychologist
        psychologists = Psychologist.objects.filter(is_active=True)[:5]
        if psychologists.exists():
            bm25_service.build_index(psychologists)
            
            test_query = "anxiety depression therapy"
            
            # First call
            start_time = time.time()
            results1 = bm25_service.search(test_query, top_k=3)
            first_call_time = time.time() - start_time
            
            # Second call
            start_time = time.time()
            results2 = bm25_service.search(test_query, top_k=3)
            second_call_time = time.time() - start_time
            
            self.stdout.write(f"First BM25 call: {first_call_time:.4f}s")
            self.stdout.write(f"Second BM25 call: {second_call_time:.4f}s")
            if second_call_time > 0:
                self.stdout.write(f"Speed improvement: {first_call_time/second_call_time:.2f}x")

    def test_embeddings(self):
        """Test embedding generation performance."""
        self.stdout.write('\nTesting embedding generation performance...')
        self.stdout.write('=' * 50)
        
        vector_service = VectorEmbeddingService()
        test_texts = [
            "Patient presenting with anxiety and depression",
            "Therapist specializing in CBT and DBT",
            "Child psychologist with autism experience",
            "Couples therapy and relationship counseling",
            "Trauma-informed care and EMDR therapy"
        ]
        
        # Test single embedding
        start_time = time.time()
        single_embedding = vector_service.generate_embedding(test_texts[0])
        single_time = time.time() - start_time
        self.stdout.write(f"Single embedding: {single_time:.4f}s")
        
        # Test batch embeddings
        start_time = time.time()
        batch_embeddings = vector_service.generate_embeddings_batch(test_texts)
        batch_time = time.time() - start_time
        self.stdout.write(f"Batch embeddings ({len(test_texts)} texts): {batch_time:.4f}s")
        self.stdout.write(f"Average per text: {batch_time/len(test_texts):.4f}s")
        
        # Test cached embeddings
        start_time = time.time()
        cached_embeddings = vector_service.generate_embeddings_batch(test_texts)
        cached_time = time.time() - start_time
        self.stdout.write(f"Cached batch embeddings: {cached_time:.4f}s")
        self.stdout.write(f"Cache speed improvement: {batch_time/cached_time:.2f}x")

    def test_bm25(self):
        """Test BM25 search performance."""
        self.stdout.write('\nTesting BM25 search performance...')
        self.stdout.write('=' * 50)
        
        from catalogue.models import Psychologist
        
        bm25_service = BM25Service()
        psychologists = Psychologist.objects.filter(is_active=True)[:10]
        
        if not psychologists.exists():
            self.stdout.write(self.style.WARNING('No psychologists found for testing'))
            return
        
        # Build index
        start_time = time.time()
        success = bm25_service.build_index(psychologists)
        build_time = time.time() - start_time
        
        if not success:
            self.stdout.write(self.style.ERROR('Failed to build BM25 index'))
            return
        
        self.stdout.write(f"Index built in: {build_time:.4f}s")
        self.stdout.write(f"Indexed {len(psychologists)} psychologists")
        
        # Test searches
        test_queries = [
            "anxiety depression",
            "CBT therapy",
            "child psychology",
            "couples counseling",
            "trauma therapy"
        ]
        
        total_time = 0
        for query in test_queries:
            start_time = time.time()
            results = bm25_service.search(query, top_k=5)
            query_time = time.time() - start_time
            total_time += query_time
            
            self.stdout.write(f"Query '{query}': {query_time:.4f}s ({len(results)} results)")
        
        avg_time = total_time / len(test_queries)
        self.stdout.write(f"Average query time: {avg_time:.4f}s")

    def test_matching(self):
        """Test full matching performance."""
        self.stdout.write('\nTesting full matching performance...')
        self.stdout.write('=' * 50)
        
        # Find a test referral
        referral = Referral.objects.filter(
            status__in=[Referral.Status.SUBMITTED, Referral.Status.MATCHING]
        ).first()
        
        if not referral:
            self.stdout.write(self.style.WARNING('No test referrals found'))
            return
        
        matching_service = MatchingService()
        
        # Test matching performance
        start_time = time.time()
        matches, routing_decision = matching_service.find_matches(referral, limit=5)
        matching_time = time.time() - start_time
        
        self.stdout.write(f"Matching completed in: {matching_time:.4f}s")
        self.stdout.write(f"Found {len(matches)} matches")
        self.stdout.write(f"Routing decision: {routing_decision['decision']}")
        self.stdout.write(f"Highest score: {routing_decision['highest_score']:.3f}")
        
        # Test cached matching (if we run it again)
        start_time = time.time()
        matches2, routing_decision2 = matching_service.find_matches(referral, limit=5)
        cached_time = time.time() - start_time
        
        self.stdout.write(f"Cached matching: {cached_time:.4f}s")
        if cached_time > 0:
            self.stdout.write(f"Cache speed improvement: {matching_time/cached_time:.2f}x")
        
        # Show cache statistics
        cache_stats = self.get_cache_stats()
        self.stdout.write(f"\nCache statistics:")
        self.stdout.write(f"Total cache keys: {cache_stats['total_keys']}")
        self.stdout.write(f"Embedding caches: {cache_stats['embedding_keys']}")
        self.stdout.write(f"BM25 caches: {cache_stats['bm25_keys']}")
        self.stdout.write(f"Threshold caches: {cache_stats['threshold_keys']}")

    def get_cache_stats(self):
        """Get cache statistics."""
        try:
            keys = cache.keys("*")
            total_keys = len(keys) if keys else 0
            
            embedding_keys = len([k for k in keys if k.startswith('embedding_')]) if keys else 0
            bm25_keys = len([k for k in keys if k.startswith('bm25_')]) if keys else 0
            threshold_keys = len([k for k in keys if k.startswith('threshold_config_')]) if keys else 0
            
            return {
                'total_keys': total_keys,
                'embedding_keys': embedding_keys,
                'bm25_keys': bm25_keys,
                'threshold_keys': threshold_keys
            }
        except Exception as e:
            self.stdout.write(f"Error getting cache stats: {e}")
            return {
                'total_keys': 0,
                'embedding_keys': 0,
                'bm25_keys': 0,
                'threshold_keys': 0
            }
