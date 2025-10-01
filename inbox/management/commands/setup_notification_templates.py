"""
Management command to set up default notification templates.
"""
from django.core.management.base import BaseCommand
from django.template.loader import get_template

from inbox.models import NotificationTemplate


class Command(BaseCommand):
    help = "Set up default notification templates"

    def handle(self, *args, **options):
        """Create default notification templates."""

        templates = [
            {
                "name": "referral_created",
                "notification_type": "referral_update",
                "title_template": "New referral created for {{ referral.patient.get_full_name }}",
                "message_template": "A new referral has been created for {{ referral.patient.get_full_name }}. Please review the details and take appropriate action.",
                "email_subject_template": "New Referral - {{ referral.patient.get_full_name }}",
                "email_body_template": "A new referral has been created for {{ referral.patient.get_full_name }}. Please review the details and take appropriate action.",
            },
            {
                "name": "referral_updated",
                "notification_type": "referral_update",
                "title_template": "Referral updated for {{ referral.patient.get_full_name }}",
                "message_template": "The referral for {{ referral.patient.get_full_name }} has been updated. Please review the changes.",
                "email_subject_template": "Referral Updated - {{ referral.patient.get_full_name }}",
                "email_body_template": "The referral for {{ referral.patient.get_full_name }} has been updated. Please review the changes.",
            },
            {
                "name": "matching_complete",
                "notification_type": "matching_complete",
                "title_template": "Matching complete for {{ referral.patient.get_full_name }}",
                "message_template": "Matching has been completed for {{ referral.patient.get_full_name }}. {{ candidates_count }} potential matches found.",
                "email_subject_template": "Matching Complete - {{ referral.patient.get_full_name }}",
                "email_body_template": "Matching has been completed for {{ referral.patient.get_full_name }}. {{ candidates_count }} potential matches found.",
            },
            {
                "name": "psychologist_invitation",
                "notification_type": "invitation",
                "title_template": "New invitation for {{ referral.patient.get_full_name }}",
                "message_template": "You have been invited to provide psychological services for {{ referral.patient.get_full_name }}. Please respond by {{ deadline }}.",
                "email_subject_template": "New Invitation - {{ referral.patient.get_full_name }}",
                "email_body_template": "You have been invited to provide psychological services for {{ referral.patient.get_full_name }}. Please respond by {{ deadline }}.",
            },
            {
                "name": "appointment_scheduled",
                "notification_type": "appointment",
                "title_template": 'Appointment scheduled for {{ appointment.appointment_date|date:"d M Y H:i" }}',
                "message_template": 'An appointment has been scheduled for {{ appointment.appointment_date|date:"d M Y H:i" }}. Please ensure you are available.',
                "email_subject_template": 'Appointment Scheduled - {{ appointment.appointment_date|date:"d M Y H:i" }}',
                "email_body_template": 'An appointment has been scheduled for {{ appointment.appointment_date|date:"d M Y H:i" }}. Please ensure you are available.',
            },
            {
                "name": "appointment_reminder",
                "notification_type": "reminder",
                "title_template": 'Appointment reminder for {{ appointment.appointment_date|date:"d M Y H:i" }}',
                "message_template": 'This is a reminder that you have an appointment scheduled for {{ appointment.appointment_date|date:"d M Y H:i" }}.',
                "email_subject_template": 'Appointment Reminder - {{ appointment.appointment_date|date:"d M Y H:i" }}',
                "email_body_template": 'This is a reminder that you have an appointment scheduled for {{ appointment.appointment_date|date:"d M Y H:i" }}.',
            },
            {
                "name": "system_maintenance",
                "notification_type": "system",
                "title_template": "System maintenance scheduled",
                "message_template": "System maintenance has been scheduled for {{ maintenance_date }}. The system will be unavailable during this time.",
                "email_subject_template": "System Maintenance - {{ maintenance_date }}",
                "email_body_template": "System maintenance has been scheduled for {{ maintenance_date }}. The system will be unavailable during this time.",
            },
            {
                "name": "welcome_message",
                "notification_type": "system",
                "title_template": "Welcome to ReferWell Direct",
                "message_template": "Welcome to ReferWell Direct! Your account has been created successfully. Please complete your profile to get started.",
                "email_subject_template": "Welcome to ReferWell Direct",
                "email_body_template": "Welcome to ReferWell Direct! Your account has been created successfully. Please complete your profile to get started.",
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data["name"], defaults=template_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created template: {template.name}")
                )
            else:
                # Update existing template
                for key, value in template_data.items():
                    if key != "name":
                        setattr(template, key, value)
                template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated template: {template.name}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {len(templates)} templates: "
                f"{created_count} created, {updated_count} updated"
            )
        )
