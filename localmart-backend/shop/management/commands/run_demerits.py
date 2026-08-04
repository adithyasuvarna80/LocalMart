from django.core.management.base import BaseCommand
from shop.cron import apply_demerits

class Command(BaseCommand):
    help = 'Manually runs the 24-hour demerit penalty check'
    def handle(self, *args, **kwargs):
        apply_demerits()
        self.stdout.write(self.style.SUCCESS("Successfully assigned demerit penalties!"))