"""
Management command to create default onboarding steps for all user types.
"""
from django.core.management.base import BaseCommand

from accounts.models import OnboardingStep


class Command(BaseCommand):
    help = "Create default onboarding steps for all user types"

    def handle(self, *args, **options):
        """Create default onboarding steps."""

        # Define default steps for each user type
        steps_data = [
            # GP Steps
            {
                "name": "welcome_gp",
                "step_type": "profile_setup",
                "user_type": "gp",
                "order": 1,
                "is_required": True,
                "description": "Welcome to ReferWell Direct - your mental health referral platform",
                "help_text": "This step introduces you to the platform and its features.",
                "is_active": True,
            },
            {
                "name": "profile_setup_gp",
                "step_type": "profile_setup",
                "user_type": "gp",
                "order": 2,
                "is_required": True,
                "description": "Set up your professional profile and practice information",
                "help_text": "Add your professional details, specializations, and practice information.",
                "is_active": True,
            },
            {
                "name": "organisation_setup_gp",
                "step_type": "organisation_setup",
                "user_type": "gp",
                "order": 3,
                "is_required": True,
                "description": "Set up your practice organization details",
                "help_text": "Configure your practice information and location.",
                "is_active": True,
            },
            # Patient Steps
            {
                "name": "welcome_patient",
                "step_type": "profile_setup",
                "user_type": "patient",
                "order": 1,
                "is_required": True,
                "description": "Welcome to ReferWell Direct - your mental health journey starts here",
                "help_text": "This step introduces you to the platform and how it can help you.",
                "is_active": True,
            },
            {
                "name": "profile_setup_patient",
                "step_type": "profile_setup",
                "user_type": "patient",
                "order": 2,
                "is_required": True,
                "description": "Set up your personal profile and preferences",
                "help_text": "Add your personal details and treatment preferences.",
                "is_active": True,
            },
            {
                "name": "preferences_patient",
                "step_type": "preferences",
                "user_type": "patient",
                "order": 3,
                "is_required": True,
                "description": "Set your treatment preferences and privacy settings",
                "help_text": "Configure your treatment preferences and privacy settings.",
                "is_active": True,
            },
            # Psychologist Steps
            {
                "name": "welcome_psychologist",
                "step_type": "profile_setup",
                "user_type": "psychologist",
                "order": 1,
                "is_required": True,
                "description": "Welcome to ReferWell Direct - join our network of mental health professionals",
                "help_text": "This step introduces you to the platform and how to get started.",
                "is_active": True,
            },
            {
                "name": "profile_setup_psychologist",
                "step_type": "profile_setup",
                "user_type": "psychologist",
                "order": 2,
                "is_required": True,
                "description": "Set up your professional profile and qualifications",
                "help_text": "Add your professional details, qualifications, and specializations.",
                "is_active": True,
            },
            {
                "name": "organisation_setup_psychologist",
                "step_type": "organisation_setup",
                "user_type": "psychologist",
                "order": 3,
                "is_required": True,
                "description": "Set up your practice organization details",
                "help_text": "Configure your practice information and location.",
                "is_active": True,
            },
            {
                "name": "verification_psychologist",
                "step_type": "verification",
                "user_type": "psychologist",
                "order": 4,
                "is_required": True,
                "description": "Complete professional verification process",
                "help_text": "Upload required documents for professional verification.",
                "is_active": True,
            },
            # Admin Steps
            {
                "name": "welcome_admin",
                "step_type": "profile_setup",
                "user_type": "admin",
                "order": 1,
                "is_required": True,
                "description": "Welcome to the ReferWell Direct administration panel",
                "help_text": "This step introduces you to the admin features and capabilities.",
                "is_active": True,
            },
            {
                "name": "system_overview_admin",
                "step_type": "preferences",
                "user_type": "admin",
                "order": 2,
                "is_required": True,
                "description": "Learn about system administration and monitoring",
                "help_text": "Understand the key admin features and system monitoring tools.",
                "is_active": True,
            },
            # High-Touch Referrer Steps
            {
                "name": "welcome_high_touch",
                "step_type": "profile_setup",
                "user_type": "high_touch_referrer",
                "order": 1,
                "is_required": True,
                "description": "Welcome to ReferWell Direct - high-touch referral management",
                "help_text": "This step introduces you to the high-touch referral features.",
                "is_active": True,
            },
            {
                "name": "profile_setup_high_touch",
                "step_type": "profile_setup",
                "user_type": "high_touch_referrer",
                "order": 2,
                "is_required": True,
                "description": "Set up your professional profile and organization details",
                "help_text": "Add your professional details and organization information.",
                "is_active": True,
            },
            {
                "name": "organisation_setup_high_touch",
                "step_type": "organisation_setup",
                "user_type": "high_touch_referrer",
                "order": 3,
                "is_required": True,
                "description": "Set up your organization details",
                "help_text": "Configure your organization information and settings.",
                "is_active": True,
            },
        ]

        created_count = 0
        updated_count = 0

        for step_data in steps_data:
            step, created = OnboardingStep.objects.get_or_create(
                name=step_data["name"], defaults=step_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created step: {step.name} for {step.user_type}"
                    )
                )
            else:
                # Update existing step
                for key, value in step_data.items():
                    if key != "name":  # Don't update the name
                        setattr(step, key, value)
                step.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Updated step: {step.name} for {step.user_type}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nOnboarding steps setup complete!\n"
                f"Created: {created_count} steps\n"
                f"Updated: {updated_count} steps\n"
                f"Total steps: {OnboardingStep.objects.count()}"
            )
        )
