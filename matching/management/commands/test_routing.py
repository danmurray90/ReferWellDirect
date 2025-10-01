"""
Management command to test threshold routing functionality.
"""
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from matching.models import MatchingThreshold
from matching.routing_service import ReferralRoutingService
from matching.services import MatchingService
from referrals.models import Referral

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test threshold routing functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--referral-id", type=str, help="Specific referral ID to test (optional)"
        )
        parser.add_argument(
            "--create-thresholds",
            action="store_true",
            help="Create default threshold configurations",
        )
        parser.add_argument(
            "--show-stats", action="store_true", help="Show routing statistics"
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Testing threshold routing functionality...")
        )

        # Create default thresholds if requested
        if options["create_thresholds"]:
            self.create_default_thresholds()

        # Show statistics if requested
        if options["show_stats"]:
            self.show_routing_statistics()
            return

        # Test specific referral or find a test referral
        if options["referral_id"]:
            try:
                referral = Referral.objects.get(id=options["referral_id"])
                self.test_referral_routing(referral)
            except Referral.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Referral {options["referral_id"]} not found')
                )
        else:
            # Find a test referral
            referral = Referral.objects.filter(
                status__in=[Referral.Status.SUBMITTED, Referral.Status.MATCHING]
            ).first()

            if referral:
                self.test_referral_routing(referral)
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "No test referrals found. Create a referral first."
                    )
                )

    def create_default_thresholds(self):
        """Create default threshold configurations."""
        self.stdout.write("Creating default threshold configurations...")

        routing_service = ReferralRoutingService()
        success = routing_service.create_default_thresholds()

        if success:
            self.stdout.write(
                self.style.SUCCESS("Default thresholds created successfully")
            )
        else:
            self.stdout.write(self.style.ERROR("Failed to create default thresholds"))

    def show_routing_statistics(self):
        """Show routing statistics."""
        self.stdout.write("Routing Statistics:")
        self.stdout.write("=" * 50)

        routing_service = ReferralRoutingService()
        stats = routing_service.get_routing_statistics()

        self.stdout.write(f"Total referrals: {stats['total_referrals']}")
        self.stdout.write(
            f"Auto-routed: {stats['auto_routed']} ({stats['auto_percentage']:.1f}%)"
        )
        self.stdout.write(
            f"High-touch routed: {stats['high_touch_routed']} ({stats['high_touch_percentage']:.1f}%)"
        )
        self.stdout.write(
            f"Manual review: {stats['manual_review']} ({stats['manual_percentage']:.1f}%)"
        )

        # Show threshold configurations
        self.stdout.write("\nThreshold Configurations:")
        self.stdout.write("-" * 30)

        thresholds = MatchingThreshold.objects.filter(is_active=True)
        for threshold in thresholds:
            self.stdout.write(
                f"{threshold.get_user_type_display()}: "
                f"Auto={threshold.auto_threshold:.2f}, "
                f"High-touch={threshold.high_touch_threshold:.2f}"
            )

    def test_referral_routing(self, referral):
        """Test routing for a specific referral."""
        self.stdout.write(f"Testing routing for referral {referral.id}...")
        self.stdout.write(f"Current status: {referral.get_status_display()}")

        # Initialize matching service
        matching_service = MatchingService()

        # Find matches and get routing decision
        matches, routing_decision = matching_service.find_matches(referral, limit=5)

        # Display results
        self.stdout.write(f"\nFound {len(matches)} matches")
        self.stdout.write(f'Routing decision: {routing_decision["decision"]}')
        self.stdout.write(f'Reason: {routing_decision["reason"]}')
        self.stdout.write(f'Highest score: {routing_decision["highest_score"]:.3f}')
        self.stdout.write(f'Auto threshold: {routing_decision["auto_threshold"]:.3f}')
        self.stdout.write(
            f'High-touch threshold: {routing_decision["high_touch_threshold"]:.3f}'
        )

        # Show top matches
        if matches:
            self.stdout.write("\nTop matches:")
            for i, match in enumerate(matches[:3], 1):
                psychologist = match["psychologist"]
                score = match["score"]
                self.stdout.write(
                    f"  {i}. {psychologist.get_full_name()} - Score: {score:.3f}"
                )

        # Refresh referral to see updated status
        referral.refresh_from_db()
        self.stdout.write(f"\nUpdated status: {referral.get_status_display()}")

        if referral.is_high_touch_queue:
            self.stdout.write(
                self.style.WARNING(
                    "Referral routed to High-Touch queue for manual review"
                )
            )
        elif referral.status == Referral.Status.SHORTLISTED:
            self.stdout.write(self.style.SUCCESS("Referral auto-routed to shortlisted"))
        else:
            self.stdout.write(self.style.WARNING("Referral requires manual review"))
