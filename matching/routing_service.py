"""
Routing service for ReferWell Direct.
Handles threshold-based routing of referrals to different queues.
"""
import logging
from typing import Any, Dict, List

from django.db import transaction
from django.db.models import Q

from matching.models import MatchingThreshold
from referrals.models import Referral

logger = logging.getLogger(__name__)


class ReferralRoutingService:
    """
    Service for routing referrals based on matching confidence scores.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def route_referral(
        self, referral: Referral, routing_decision: dict[str, Any]
    ) -> bool:
        """
        Route a referral based on the routing decision.

        Args:
            referral: The referral to route
            routing_decision: Dictionary containing routing decision details

        Returns:
            True if routing was successful, False otherwise
        """
        try:
            with transaction.atomic():
                decision = routing_decision.get("decision", "manual_review")

                if decision == "auto":
                    # Auto-route: referral can proceed with automatic matching
                    referral.status = Referral.Status.SHORTLISTED
                    self.logger.info(
                        f"Auto-routed referral {referral.id} to shortlisted"
                    )

                elif decision == "high_touch":
                    # High-touch route: needs human review
                    referral.status = Referral.Status.HIGH_TOUCH_QUEUE
                    self.logger.info(
                        f"High-touch routed referral {referral.id} to queue"
                    )

                else:  # manual_review
                    # Manual review: needs human intervention
                    referral.status = Referral.Status.MATCHING
                    self.logger.info(
                        f"Manual review required for referral {referral.id}"
                    )

                # Add routing information to referral metadata
                if not hasattr(referral, "routing_metadata"):
                    referral.routing_metadata = {}

                referral.routing_metadata.update(
                    {
                        "routing_decision": routing_decision,
                        "routed_at": referral.updated_at.isoformat()
                        if referral.updated_at
                        else None,
                    }
                )

                referral.save(
                    update_fields=["status", "routing_metadata", "updated_at"]
                )

                self.logger.info(
                    f"Successfully routed referral {referral.id} with decision: {decision}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Failed to route referral {referral.id}: {e}")
            return False

    def get_high_touch_queue(self, limit: int = 50) -> list[Referral]:
        """
        Get referrals in the high-touch queue.

        Args:
            limit: Maximum number of referrals to return

        Returns:
            List of referrals in high-touch queue
        """
        return list(
            Referral.objects.filter(status=Referral.Status.HIGH_TOUCH_QUEUE).order_by(
                "created_at"
            )[:limit]
        )

    def get_routing_statistics(self) -> dict[str, Any]:
        """
        Get statistics about referral routing.

        Returns:
            Dictionary with routing statistics
        """
        from django.db.models import Count

        stats = Referral.objects.aggregate(
            total_referrals=Count("id"),
            auto_routed=Count("id", filter=Q(status=Referral.Status.SHORTLISTED)),
            high_touch_routed=Count(
                "id", filter=Q(status=Referral.Status.HIGH_TOUCH_QUEUE)
            ),
            manual_review=Count("id", filter=Q(status=Referral.Status.MATCHING)),
        )

        return {
            "total_referrals": stats["total_referrals"],
            "auto_routed": stats["auto_routed"],
            "high_touch_routed": stats["high_touch_routed"],
            "manual_review": stats["manual_review"],
            "auto_percentage": (stats["auto_routed"] / stats["total_referrals"] * 100)
            if stats["total_referrals"] > 0
            else 0,
            "high_touch_percentage": (
                stats["high_touch_routed"] / stats["total_referrals"] * 100
            )
            if stats["total_referrals"] > 0
            else 0,
            "manual_percentage": (
                stats["manual_review"] / stats["total_referrals"] * 100
            )
            if stats["total_referrals"] > 0
            else 0,
        }

    def create_default_thresholds(self) -> bool:
        """
        Create default threshold configurations for all user types.

        Returns:
            True if successful, False otherwise
        """
        try:
            default_thresholds = [
                {
                    "user_type": "gp",
                    "auto_threshold": 0.7,
                    "high_touch_threshold": 0.5,
                },
                {
                    "user_type": "patient",
                    "auto_threshold": 0.8,
                    "high_touch_threshold": 0.6,
                },
                {
                    "user_type": "psychologist",
                    "auto_threshold": 0.6,
                    "high_touch_threshold": 0.4,
                },
                {
                    "user_type": "admin",
                    "auto_threshold": 0.5,
                    "high_touch_threshold": 0.3,
                },
            ]

            for threshold_data in default_thresholds:
                MatchingThreshold.objects.get_or_create(
                    user_type=threshold_data["user_type"], defaults=threshold_data
                )

            self.logger.info("Created default threshold configurations")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create default thresholds: {e}")
            return False

    def invalidate_threshold_cache(self, user_type: str | None = None) -> None:
        """
        Invalidate threshold configuration cache.

        Args:
            user_type: Specific user type to invalidate (if None, invalidates all)
        """
        from django.core.cache import cache

        if user_type:
            cache_key = f"threshold_config_{user_type}"
            cache.delete(cache_key)
            self.logger.info(f"Invalidated threshold cache for user type: {user_type}")
        else:
            # Invalidate all threshold caches
            user_types = ["gp", "patient", "psychologist", "admin"]
            for ut in user_types:
                cache_key = f"threshold_config_{ut}"
                cache.delete(cache_key)
            self.logger.info("Invalidated all threshold caches")

    def clear_all_caches(self) -> None:
        """
        Clear all matching-related caches.
        """
        from django.core.cache import cache

        # Clear embedding caches
        cache.delete_many(cache.keys("embedding_*"))  # type: ignore[attr-defined]

        # Clear BM25 caches
        cache.delete_many(cache.keys("bm25_*"))  # type: ignore[attr-defined]

        # Clear threshold caches
        cache.delete_many(cache.keys("threshold_config_*"))  # type: ignore[attr-defined]

        self.logger.info("Cleared all matching-related caches")
