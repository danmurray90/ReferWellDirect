"""
Matching services for ReferWell Direct.
"""
from typing import List, Dict, Any, Optional
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models import Q
from django.db.models import QuerySet, F
from catalogue.models import Psychologist
from referrals.models import Referral
import logging

logger = logging.getLogger(__name__)


class FeasibilityFilter:
    """
    Feasibility filter for psychologist matching.
    
    This filter applies basic criteria to narrow down the pool of psychologists
    before more expensive operations like vector similarity search.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def filter_psychologists(
        self, 
        referral: Referral, 
        psychologists: Optional[QuerySet[Psychologist]] = None
    ) -> QuerySet[Psychologist]:
        """
        Filter psychologists based on feasibility criteria.
        
        Args:
            referral: The referral to match against
            psychologists: Optional queryset to filter (defaults to all active psychologists)
            
        Returns:
            Filtered queryset of psychologists
        """
        if psychologists is None:
            psychologists = Psychologist.objects.filter(
                is_active=True,
                is_accepting_referrals=True
            )
        
        self.logger.info(f"Starting feasibility filter for referral {referral.id}")
        initial_count = psychologists.count()
        
        # Apply filters in order of selectivity (most selective first)
        psychologists = self._filter_by_service_type(psychologists, referral)
        psychologists = self._filter_by_modality(psychologists, referral)
        psychologists = self._filter_by_availability(psychologists, referral)
        psychologists = self._filter_by_radius(psychologists, referral)
        psychologists = self._filter_by_capacity(psychologists, referral)
        
        final_count = psychologists.count()
        self.logger.info(
            f"Feasibility filter complete: {initial_count} -> {final_count} psychologists"
        )
        
        return psychologists
    
    def _filter_by_service_type(
        self, 
        psychologists: QuerySet[Psychologist], 
        referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by NHS/private service type preference."""
        if not referral.service_type:
            return psychologists
        
        if referral.service_type == 'nhs':
            return psychologists.filter(service_type__in=['nhs', 'mixed'])
        elif referral.service_type == 'private':
            return psychologists.filter(service_type__in=['private', 'mixed'])
        
        return psychologists
    
    def _filter_by_modality(
        self, 
        psychologists: QuerySet[Psychologist], 
        referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by remote vs in-person modality preference."""
        if not referral.modality:
            return psychologists
        
        if referral.modality == 'remote':
            return psychologists.filter(modality__in=['remote', 'mixed'])
        elif referral.modality == 'in_person':
            return psychologists.filter(modality__in=['in_person', 'mixed'])
        
        return psychologists
    
    def _filter_by_availability(
        self, 
        psychologists: QuerySet[Psychologist], 
        referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by availability status."""
        return psychologists.filter(
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE
        )
    
    def _filter_by_radius(
        self, 
        psychologists: QuerySet[Psychologist], 
        referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by geographic radius using PostGIS."""
        if not referral.preferred_latitude or not referral.preferred_longitude:
            self.logger.warning("No patient location provided for radius filtering")
            return psychologists
        
        if not referral.max_distance_km:
            self.logger.warning("No max distance specified for radius filtering")
            return psychologists
        
        # Convert km to meters
        max_distance_meters = referral.max_distance_km * 1000
        
        # Create point from patient location
        patient_point = Point(
            referral.preferred_longitude, 
            referral.preferred_latitude, 
            srid=4326
        )
        
        # Filter using PostGIS ST_DWithin for efficient radius queries
        return psychologists.filter(
            location__isnull=False
        ).filter(
            location__dwithin=(patient_point, max_distance_meters)
        )
    
    def _filter_by_capacity(
        self, 
        psychologists: QuerySet[Psychologist], 
        referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by psychologist capacity."""
        return psychologists.filter(
            current_patients__lt=F('max_patients')
        )


class MatchingService:
    """
    Main matching service that orchestrates the matching process.
    """
    
    def __init__(self):
        self.feasibility_filter = FeasibilityFilter()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def find_matches(
        self, 
        referral: Referral, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find matching psychologists for a referral.
        
        Args:
            referral: The referral to match
            limit: Maximum number of matches to return
            
        Returns:
            List of match dictionaries with psychologist and score
        """
        self.logger.info(f"Starting matching process for referral {referral.id}")
        
        # Step 1: Apply feasibility filter
        feasible_psychologists = self.feasibility_filter.filter_psychologists(referral)
        
        if not feasible_psychologists.exists():
            self.logger.warning(f"No feasible psychologists found for referral {referral.id}")
            return []
        
        # Step 2: Apply additional filters (to be implemented)
        # - Specialism matching
        # - Language matching
        # - Age group preferences
        
        # Step 3: Calculate similarity scores (to be implemented)
        # - Vector similarity
        # - Structured feature matching
        
        # Step 4: Rerank and return top matches
        matches = []
        for psychologist in feasible_psychologists[:limit]:
            match = {
                'psychologist': psychologist,
                'score': 0.0,  # Placeholder
                'explanation': {
                    'feasibility_passed': True,
                    'service_type_match': True,
                    'modality_match': True,
                    'radius_match': True,
                    'capacity_available': True,
                }
            }
            matches.append(match)
        
        self.logger.info(f"Found {len(matches)} matches for referral {referral.id}")
        return matches
