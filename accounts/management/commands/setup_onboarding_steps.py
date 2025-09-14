"""
Management command to set up default onboarding steps.
"""
from django.core.management.base import BaseCommand
from accounts.models import OnboardingStep


class Command(BaseCommand):
    help = 'Set up default onboarding steps for all user types'

    def handle(self, *args, **options):
        """Create default onboarding steps."""
        
        # Define onboarding steps for each user type
        steps_data = [
            # GP Steps
            {
                'user_type': 'gp',
                'steps': [
                    {
                        'name': 'Profile Setup',
                        'step_type': 'profile_setup',
                        'order': 1,
                        'is_required': True,
                        'description': 'Set up your basic profile information',
                        'help_text': 'This information helps us personalize your experience and verify your identity.'
                    },
                    {
                        'name': 'Practice Setup',
                        'step_type': 'organisation_setup',
                        'order': 2,
                        'is_required': True,
                        'description': 'Add your practice or organisation details',
                        'help_text': 'This helps us understand your practice context and provide relevant services.'
                    },
                    {
                        'name': 'Preferences',
                        'step_type': 'preferences',
                        'order': 3,
                        'is_required': False,
                        'description': 'Customize your experience',
                        'help_text': 'Set your notification preferences and other personal settings.'
                    },
                    {
                        'name': 'Verification',
                        'step_type': 'verification',
                        'order': 4,
                        'is_required': True,
                        'description': 'Verify your professional credentials',
                        'help_text': 'Verify your GMC registration and practice details for security.'
                    },
                    {
                        'name': 'Welcome',
                        'step_type': 'completion',
                        'order': 5,
                        'is_required': True,
                        'description': 'Welcome to ReferWell Direct',
                        'help_text': 'Complete your setup and start using the service.'
                    }
                ]
            },
            # Patient Steps
            {
                'user_type': 'patient',
                'steps': [
                    {
                        'name': 'Profile Setup',
                        'step_type': 'profile_setup',
                        'order': 1,
                        'is_required': True,
                        'description': 'Set up your basic profile information',
                        'help_text': 'This information helps us personalize your experience and match you with suitable services.'
                    },
                    {
                        'name': 'Preferences',
                        'step_type': 'preferences',
                        'order': 2,
                        'is_required': False,
                        'description': 'Customize your experience',
                        'help_text': 'Set your notification preferences and privacy settings.'
                    },
                    {
                        'name': 'Welcome',
                        'step_type': 'completion',
                        'order': 3,
                        'is_required': True,
                        'description': 'Welcome to ReferWell Direct',
                        'help_text': 'Complete your setup and start finding the right mental health support.'
                    }
                ]
            },
            # Psychologist Steps
            {
                'user_type': 'psychologist',
                'steps': [
                    {
                        'name': 'Profile Setup',
                        'step_type': 'profile_setup',
                        'order': 1,
                        'is_required': True,
                        'description': 'Set up your basic profile information',
                        'help_text': 'This information helps us personalize your experience and verify your identity.'
                    },
                    {
                        'name': 'Practice Setup',
                        'step_type': 'organisation_setup',
                        'order': 2,
                        'is_required': True,
                        'description': 'Add your practice or organisation details',
                        'help_text': 'This helps us understand your practice context and provide relevant services.'
                    },
                    {
                        'name': 'Preferences',
                        'step_type': 'preferences',
                        'order': 3,
                        'is_required': False,
                        'description': 'Customize your experience',
                        'help_text': 'Set your notification preferences and other personal settings.'
                    },
                    {
                        'name': 'Verification',
                        'step_type': 'verification',
                        'order': 4,
                        'is_required': True,
                        'description': 'Verify your professional credentials',
                        'help_text': 'Verify your HCPC registration or BPS membership for security.'
                    },
                    {
                        'name': 'Welcome',
                        'step_type': 'completion',
                        'order': 5,
                        'is_required': True,
                        'description': 'Welcome to ReferWell Direct',
                        'help_text': 'Complete your setup and start receiving referrals.'
                    }
                ]
            },
            # Admin Steps
            {
                'user_type': 'admin',
                'steps': [
                    {
                        'name': 'Profile Setup',
                        'step_type': 'profile_setup',
                        'order': 1,
                        'is_required': True,
                        'description': 'Set up your basic profile information',
                        'help_text': 'This information helps us personalize your experience.'
                    },
                    {
                        'name': 'Welcome',
                        'step_type': 'completion',
                        'order': 2,
                        'is_required': True,
                        'description': 'Welcome to ReferWell Direct',
                        'help_text': 'Complete your setup and start managing the system.'
                    }
                ]
            },
            # High-Touch Referrer Steps
            {
                'user_type': 'high_touch_referrer',
                'steps': [
                    {
                        'name': 'Profile Setup',
                        'step_type': 'profile_setup',
                        'order': 1,
                        'is_required': True,
                        'description': 'Set up your basic profile information',
                        'help_text': 'This information helps us personalize your experience and verify your identity.'
                    },
                    {
                        'name': 'Organisation Setup',
                        'step_type': 'organisation_setup',
                        'order': 2,
                        'is_required': True,
                        'description': 'Add your organisation details',
                        'help_text': 'This helps us understand your organisation context and provide relevant services.'
                    },
                    {
                        'name': 'Preferences',
                        'step_type': 'preferences',
                        'order': 3,
                        'is_required': False,
                        'description': 'Customize your experience',
                        'help_text': 'Set your notification preferences and other personal settings.'
                    },
                    {
                        'name': 'Verification',
                        'step_type': 'verification',
                        'order': 4,
                        'is_required': True,
                        'description': 'Verify your professional credentials',
                        'help_text': 'Verify your professional credentials for security.'
                    },
                    {
                        'name': 'Welcome',
                        'step_type': 'completion',
                        'order': 5,
                        'is_required': True,
                        'description': 'Welcome to ReferWell Direct',
                        'help_text': 'Complete your setup and start managing referrals.'
                    }
                ]
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for user_type_data in steps_data:
            user_type = user_type_data['user_type']
            steps = user_type_data['steps']
            
            self.stdout.write(f'Setting up onboarding steps for {user_type}...')
            
            for step_data in steps:
                step, created = OnboardingStep.objects.get_or_create(
                    user_type=user_type,
                    order=step_data['order'],
                    defaults={
                        'name': step_data['name'],
                        'step_type': step_data['step_type'],
                        'is_required': step_data['is_required'],
                        'description': step_data['description'],
                        'help_text': step_data['help_text'],
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  Created: {step.name}')
                else:
                    # Update existing step
                    step.name = step_data['name']
                    step.step_type = step_data['step_type']
                    step.is_required = step_data['is_required']
                    step.description = step_data['description']
                    step.help_text = step_data['help_text']
                    step.is_active = True
                    step.save()
                    updated_count += 1
                    self.stdout.write(f'  Updated: {step.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up onboarding steps: {created_count} created, {updated_count} updated'
            )
        )
