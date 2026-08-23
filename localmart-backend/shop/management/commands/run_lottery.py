from django.core.management.base import BaseCommand
from shop.cron import run_lottery_draw

class Command(BaseCommand):
    help = 'Manually triggers the daily 11 PM Token Lottery Draw for customer rewards'

    def handle(self, *args, **kwargs):
        self.stdout.write("Running Token Lottery Draw...")
        run_lottery_draw()
        self.stdout.write(self.style.SUCCESS("Successfully completed the daily Token Lottery Draw!"))