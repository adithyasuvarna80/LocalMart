from django.core.management.base import BaseCommand
from shop.cron import calculate_platform_scores

class Command(BaseCommand):
    help = 'Manually runs the midnight platform score calculation (Windows alternative to cron)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting Platform Score calculations...")
        
        # This calls the exact logic we wrote in cron.py!
        calculate_platform_scores()
        
        self.stdout.write(self.style.SUCCESS("Successfully updated all vendor platform scores!"))