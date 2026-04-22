"""
Export BehaviorEvent records from the database to a CSV file
compatible with the existing ML training pipeline (preprocess.py / train.py).

Usage:
    python manage.py export_events                          # Export to default path
    python manage.py export_events --output /app/data/live_events.csv
    python manage.py export_events --merge                  # Merge with existing synthetic data
"""
import csv
import os
from django.core.management.base import BaseCommand
from api.models import BehaviorEvent


class Command(BaseCommand):
    help = 'Export BehaviorEvent records to CSV for ML training'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output CSV file path (default: data/live_events.csv)',
        )
        parser.add_argument(
            '--merge',
            action='store_true',
            help='Merge with existing data_user500.csv into a combined file',
        )

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)

        output_path = options['output'] or os.path.join(data_dir, 'live_events.csv')

        events = BehaviorEvent.objects.all().order_by('user_id', 'timestamp')
        total = events.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No events to export.'))
            return

        # Write live events CSV
        fieldnames = ['user_id', 'product_id', 'action', 'timestamp']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for event in events.iterator(chunk_size=1000):
                writer.writerow({
                    'user_id': event.user_id,
                    'product_id': event.product_id,
                    'action': event.action,
                    'timestamp': event.timestamp.isoformat(),
                })

        self.stdout.write(self.style.SUCCESS(f'Exported {total} events to {output_path}'))

        # Optionally merge with synthetic data
        if options['merge']:
            synthetic_path = os.path.join(data_dir, 'data_user500.csv')
            merged_path = os.path.join(data_dir, 'data_merged.csv')

            if not os.path.exists(synthetic_path):
                self.stdout.write(self.style.WARNING(
                    f'Synthetic data not found at {synthetic_path}, skipping merge.'
                ))
                return

            # Read synthetic data
            rows = []
            with open(synthetic_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)

            # Read live events
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)

            # Sort by user_id, timestamp
            rows.sort(key=lambda r: (int(r['user_id']), r['timestamp']))

            # Write merged file
            with open(merged_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            self.stdout.write(self.style.SUCCESS(
                f'Merged {len(rows)} total records to {merged_path}'
            ))
