import os

from django.core.management.base import BaseCommand

from graph.neo4j_client import Neo4jRecommender


class Command(BaseCommand):
    help = "Build Neo4j knowledge graph from existing seed data and model artifact."

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Clear Neo4j before rebuilding the graph.",
        )

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        data_dir = os.path.join(base_dir, "data")
        models_dir = os.path.join(base_dir, "models")

        uri = os.environ.get("NEO4J_URI", "bolt://db-neo4j:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")

        csv_path = os.path.join(data_dir, "data_user500.csv")
        books_path = os.path.join(data_dir, "books.json")
        users_path = os.path.join(data_dir, "users.json")
        model_path = os.path.join(models_dir, "model_best.pt")

        client = Neo4jRecommender(uri, user, password)
        try:
            if options["full"]:
                self.stdout.write("Clearing Neo4j graph...")
                client.clear_database()

            stats = client.build_graph(
                csv_path=csv_path,
                books_path=books_path,
                users_path=users_path,
                model_path=model_path,
            )
        finally:
            client.close()

        self.stdout.write(self.style.SUCCESS("Neo4j graph build completed."))
        for key, value in stats.items():
            self.stdout.write(f"- {key}: {value}")
