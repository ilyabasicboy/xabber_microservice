from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections, DatabaseError
from django.db.models import Min

from collections import defaultdict

from xabber_microservice.api.models import Account


class Command(BaseCommand):
    help = 'Delete old message history'
    db_name = settings.XMPP_SERVER_DB

    def handle(self, *args, **options):
        self.stdout.write("Starting message history cleanup task...")

        try:
            accounts = Account.objects.all()

            min_message_retention = accounts.exclude(unlimited=True).aggregate(Min('message_retention')).get('message_retention__min')
            if min_message_retention is None:
                self.stdout.write("No accounts with limited message retention found. Nothing to delete.")
                return

            self.stdout.write(f"Minimum message retention among limited accounts: {min_message_retention} days")

            paid_accounts = accounts.filter(message_retention__gt=min_message_retention) | accounts.filter(unlimited=True)
            paid_accounts_jid_list = list(paid_accounts.values_list('jid', flat=True))

            self.stdout.write(f"Found {len(paid_accounts_jid_list)} paid accounts. Cleaning up free accounts...")

            self.delete_free_accounts_messages(min_message_retention, paid_accounts_jid_list)

            accounts_to_clear_groups = defaultdict(list)
            accounts_to_clear = paid_accounts.exclude(unlimited=True)

            for account in accounts_to_clear:
                accounts_to_clear_groups[account.message_retention].append(account.jid)

            for message_retention, jid_list in accounts_to_clear_groups.items():
                self.stdout.write(f"Cleaning {len(jid_list)} accounts with retention = {message_retention} days")
                self.delete_accounts_messages(message_retention, jid_list)

            self.stdout.write("Message history cleanup completed successfully.")

        except Exception as e:
            self.stderr.write(f"Error during message cleanup: {e}")

    def delete_free_accounts_messages(self, min_message_retention: int, jid_list: list):
        try:
            with connections[self.db_name].cursor() as cursor:
                sql = """
                    DELETE FROM archive
                    WHERE 
                        TO_TIMESTAMP(timestamp / 1000000.0) < NOW() - INTERVAL '%s days'
                        AND (username || '@' || server_host) NOT IN %s
                """
                cursor.execute(sql, [min_message_retention, tuple(jid_list)])
                self.stdout.write(f"Deleted messages for free accounts older than {min_message_retention} days.")
        except DatabaseError as e:
            self.stderr.write(f"Database error during free account cleanup: {e}")

    def delete_accounts_messages(self, message_retention: int, jid_list: list):
        try:
            with connections[self.db_name].cursor() as cursor:
                sql = """
                    DELETE FROM archive
                    WHERE 
                        TO_TIMESTAMP(timestamp / 1000000.0) < NOW() - INTERVAL '%s days'
                        AND (username || '@' || server_host) IN %s
                """
                cursor.execute(sql, [message_retention, tuple(jid_list)])
                self.stdout.write(f"Deleted messages for {len(jid_list)} accounts older than {message_retention} days.")
        except DatabaseError as e:
            self.stderr.write(f"Database error during paid account cleanup: {e}")
