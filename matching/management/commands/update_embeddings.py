"""
Management command to update embeddings for psychologists.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogue.models import Psychologist
from matching.services import VectorEmbeddingService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update vector embeddings for psychologists"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of psychologists to process in each batch",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update even if embedding already exists",
        )
        parser.add_argument(
            "--psychologist-id",
            type=str,
            help="Update embedding for specific psychologist ID",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        force = options["force"]
        psychologist_id = options["psychologist_id"]

        try:
            # Initialize embedding service
            embedding_service = VectorEmbeddingService()

            if psychologist_id:
                # Update specific psychologist
                self.update_single_psychologist(
                    embedding_service, psychologist_id, force
                )
            else:
                # Update all psychologists
                self.update_all_psychologists(embedding_service, batch_size, force)

        except Exception as e:
            raise CommandError(f"Failed to update embeddings: {e}")

    def update_single_psychologist(self, embedding_service, psychologist_id, force):
        """Update embedding for a single psychologist."""
        try:
            psychologist = Psychologist.objects.get(id=psychologist_id)

            if not force and psychologist.embedding:
                self.stdout.write(
                    self.style.WARNING(
                        f"Psychologist {psychologist_id} already has embedding. Use --force to update."
                    )
                )
                return

            success = embedding_service.update_psychologist_embedding(psychologist)

            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully updated embedding for psychologist {psychologist_id}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to update embedding for psychologist {psychologist_id}"
                    )
                )

        except Psychologist.DoesNotExist:
            raise CommandError(f"Psychologist with ID {psychologist_id} not found")

    def update_all_psychologists(self, embedding_service, batch_size, force):
        """Update embeddings for all psychologists."""
        # Get psychologists to update
        if force:
            psychologists = Psychologist.objects.filter(is_active=True)
        else:
            psychologists = Psychologist.objects.filter(
                is_active=True, embedding__isnull=True
            )

        total_count = psychologists.count()

        if total_count == 0:
            self.stdout.write(
                self.style.WARNING("No psychologists need embedding updates")
            )
            return

        self.stdout.write(f"Updating embeddings for {total_count} psychologists...")

        updated_count = 0
        failed_count = 0

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = psychologists[i : i + batch_size]

            with transaction.atomic():
                for psychologist in batch:
                    try:
                        success = embedding_service.update_psychologist_embedding(
                            psychologist
                        )

                        if success:
                            updated_count += 1
                        else:
                            failed_count += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f"Failed to update embedding for psychologist {psychologist.id}"
                                )
                            )

                    except Exception as e:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error updating psychologist {psychologist.id}: {e}"
                            )
                        )

            # Progress update
            processed = min(i + batch_size, total_count)
            self.stdout.write(f"Processed {processed}/{total_count} psychologists...")

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"Embedding update complete: {updated_count} updated, {failed_count} failed"
            )
        )
