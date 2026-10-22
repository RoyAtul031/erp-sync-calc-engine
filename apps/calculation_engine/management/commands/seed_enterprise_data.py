from django.core.management.base import BaseCommand
from apps.calculation_engine.seed_data import seed_all_reference_data


class Command(BaseCommand):
    help = "Seeds standard ESG compliance frameworks, emission factors, formula methodologies, and default ERP connectors."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding enterprise ESG compliance reference data..."))
        seed_all_reference_data()
        self.stdout.write(self.style.SUCCESS("Successfully seeded compliance frameworks, emission factors, and ERP connectors!"))
