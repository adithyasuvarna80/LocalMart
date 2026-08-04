from django.core.management.base import BaseCommand
from shop.cron import apply_stock_nudges

class Command(BaseCommand):
    help = 'Manually runs the 12-hour stock nudge check'
    def handle(self, *args, **kwargs):
        apply_stock_nudges()
        self.stdout.write(self.style.SUCCESS("Successfully ran stock nudges!"))