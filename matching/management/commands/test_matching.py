"""
Management command to test the matching system.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from catalogue.models import Psychologist
from referrals.models import Referral
from matching.services import MatchingService, VectorEmbeddingService
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the matching system with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample data for testing'
        )
        parser.add_argument(
            '--test-matching',
            action='store_true',
            help='Test the matching system'
        )

    def handle(self, *args, **options):
        if options['create_sample_data']:
            self.create_sample_data()
        
        if options['test_matching']:
            self.test_matching()

    def create_sample_data(self):
        """Create sample data for testing."""
        self.stdout.write('Creating sample data...')
        
        # Create GP user
        gp_user, created = User.objects.get_or_create(
            email='gp@test.com',
            defaults={
                'first_name': 'Dr. John',
                'last_name': 'Smith',
                'role': 'gp'
            }
        )
        if created:
            gp_user.set_password('testpass123')
            gp_user.save()
        
        # Create sample psychologists
        psychologists_data = [
            {
                'email': 'psych1@test.com',
                'first_name': 'Dr. Jane',
                'last_name': 'Doe',
                'specialisms': ['anxiety', 'depression'],
                'qualifications': ['PhD', 'Clinical Psychology'],
                'service_type': 'nhs',
                'modality': 'mixed',
                'latitude': 51.5074,
                'longitude': -0.1276,
            },
            {
                'email': 'psych2@test.com',
                'first_name': 'Dr. Bob',
                'last_name': 'Wilson',
                'specialisms': ['trauma', 'ptsd'],
                'qualifications': ['MSc', 'CBT'],
                'service_type': 'private',
                'modality': 'remote',
                'latitude': 51.5074,
                'longitude': -0.1276,
            },
            {
                'email': 'psych3@test.com',
                'first_name': 'Dr. Sarah',
                'last_name': 'Brown',
                'specialisms': ['anxiety', 'ocd'],
                'qualifications': ['DClinPsy'],
                'service_type': 'mixed',
                'modality': 'in_person',
                'latitude': 51.5074,
                'longitude': -0.1276,
            }
        ]
        
        for psych_data in psychologists_data:
            user, created = User.objects.get_or_create(
                email=psych_data['email'],
                defaults={
                    'first_name': psych_data['first_name'],
                    'last_name': psych_data['last_name'],
                    'role': 'psychologist'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            
            psychologist, created = Psychologist.objects.get_or_create(
                user=user,
                defaults={
                    'specialisms': psych_data['specialisms'],
                    'qualifications': psych_data['qualifications'],
                    'service_type': psych_data['service_type'],
                    'modality': psych_data['modality'],
                    'latitude': psych_data['latitude'],
                    'longitude': psych_data['longitude'],
                    'max_patients': 50,
                    'current_patients': 25,
                    'availability_status': Psychologist.AvailabilityStatus.AVAILABLE,
                    'is_active': True,
                    'is_accepting_referrals': True
                }
            )
            
            if created:
                psychologist.update_location()
                self.stdout.write(f'Created psychologist: {psychologist.user.get_full_name()}')
        
        # Create sample referral
        referral, created = Referral.objects.get_or_create(
            referrer=gp_user,
            patient_first_name='Patient',
            patient_last_name='Test',
            defaults={
                'condition_description': 'Anxiety and depression symptoms',
                'service_type': 'nhs',
                'modality': 'mixed',
                'preferred_latitude': 51.5074,
                'preferred_longitude': -0.1276,
                'max_distance_km': 50,
                'required_specialisms': ['anxiety'],
                'language_requirements': ['en']
            }
        )
        
        if created:
            self.stdout.write(f'Created referral: {referral.id}')
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully')
        )

    def test_matching(self):
        """Test the matching system."""
        self.stdout.write('Testing matching system...')
        
        try:
            # Get a referral to test with
            referral = Referral.objects.first()
            if not referral:
                raise CommandError('No referrals found. Run with --create-sample-data first.')
            
            # Initialize matching service
            matching_service = MatchingService()
            
            # Test basic matching
            self.stdout.write('Testing basic matching...')
            basic_matches = matching_service.find_matches(referral, use_hybrid=False)
            
            self.stdout.write(f'Found {len(basic_matches)} basic matches:')
            for i, match in enumerate(basic_matches, 1):
                psych = match['psychologist']
                self.stdout.write(
                    f'  {i}. {psych.user.get_full_name()} - Score: {match["score"]:.3f}'
                )
            
            # Test hybrid matching
            self.stdout.write('\nTesting hybrid matching...')
            hybrid_matches = matching_service.find_matches(referral, use_hybrid=True)
            
            self.stdout.write(f'Found {len(hybrid_matches)} hybrid matches:')
            for i, match in enumerate(hybrid_matches, 1):
                psych = match['psychologist']
                vector_score = match.get('vector_score', 0.0)
                bm25_score = match.get('bm25_score', 0.0)
                self.stdout.write(
                    f'  {i}. {psych.user.get_full_name()} - Score: {match["score"]:.3f} '
                    f'(Vector: {vector_score:.3f}, BM25: {bm25_score:.3f})'
                )
            
            # Test embedding generation
            self.stdout.write('\nTesting embedding generation...')
            embedding_service = VectorEmbeddingService()
            
            psychologists = Psychologist.objects.filter(is_active=True)
            updated_count = 0
            
            for psychologist in psychologists:
                if embedding_service.update_psychologist_embedding(psychologist):
                    updated_count += 1
            
            self.stdout.write(f'Updated embeddings for {updated_count} psychologists')
            
            self.stdout.write(
                self.style.SUCCESS('Matching system test completed successfully')
            )
            
        except Exception as e:
            raise CommandError(f'Matching test failed: {e}')
