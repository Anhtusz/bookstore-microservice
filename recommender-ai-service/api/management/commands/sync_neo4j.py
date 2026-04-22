"""
Sync BehaviorEvent records from PostgreSQL into the Neo4j knowledge graph.

Usage:
    python manage.py sync_neo4j          # Sync only un-synced events
    python manage.py sync_neo4j --full   # Clear graph and rebuild from all events
"""
import os
from django.core.management.base import BaseCommand
from api.models import BehaviorEvent
from graph.neo4j_client import Neo4jRecommender


class Command(BaseCommand):
    help = 'Synchronize BehaviorEvent records into Neo4j knowledge graph'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Clear Neo4j and rebuild the entire graph from all events',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Number of events to process per batch (default: 500)',
        )

    def handle(self, *args, **options):
        uri = os.environ.get('NEO4J_URI', 'bolt://db-neo4j:7687')
        user = os.environ.get('NEO4J_USER', 'neo4j')
        password = os.environ.get('NEO4J_PASSWORD', 'password')

        client = Neo4jRecommender(uri, user, password)

        try:
            if options['full']:
                self._full_rebuild(client)
            else:
                self._incremental_sync(client, options['batch_size'])
        finally:
            client.close()

    def _full_rebuild(self, client):
        self.stdout.write('Clearing Neo4j database...')
        client.clear_database()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        data_dir = os.path.join(base_dir, 'data')
        models_dir = os.path.join(base_dir, 'models')
        client.build_graph(
            csv_path=os.path.join(data_dir, 'data_user500.csv'),
            books_path=os.path.join(data_dir, 'books.json'),
            users_path=os.path.join(data_dir, 'users.json'),
            model_path=os.path.join(models_dir, 'model_best.pt'),
        )

        events = BehaviorEvent.objects.all()
        total = events.count()
        self.stdout.write(f'Rebuilding graph from {total} events...')

        self._push_events_to_neo4j(client, events)

        # Mark all as synced
        BehaviorEvent.objects.all().update(synced_to_neo4j=True)
        self.stdout.write(self.style.SUCCESS(f'Full rebuild complete: {total} events synced.'))

    def _incremental_sync(self, client, batch_size):
        events = BehaviorEvent.objects.filter(synced_to_neo4j=False)
        total = events.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No new events to sync.'))
            return

        self.stdout.write(f'Syncing {total} new events to Neo4j...')
        self._push_events_to_neo4j(client, events)

        # Mark as synced
        events.update(synced_to_neo4j=True)
        self.stdout.write(self.style.SUCCESS(f'Incremental sync complete: {total} events synced.'))

    def _push_events_to_neo4j(self, client, events_qs):
        """Push events into Neo4j by creating/merging User/Book and required relationships."""
        rows = [
            {
                'user_id': e.user_id,
                'product_id': e.product_id,
                'action': e.action,
                'timestamp': e.timestamp.isoformat(),
            }
            for e in events_qs
        ]
        client.sync_behavior_events(rows)
