from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create groups'

    def handle(self, *args, **options):
        group = Group(name='Logistics')
        group.save()
        permission = Permission.objects.filter(codename__endswith='logistics')
        for permission in permission:
            group.permissions.add(permission)
        permission = Permission.objects.filter(codename__endswith='logisticsuploads')
        for permission in permission:
            group.permissions.add(permission)
        permission = Permission.objects.filter(codename__endswith='financial')
        for permission in permission:
            group.permissions.add(permission)
        group.save()
        group = Group(name='Financial')
        group.save()
        permission = Permission.objects.filter(codename__endswith='financial')
        for permission in permission:
            group.permissions.add(permission)
        permission = Permission.objects.filter(codename="view_logisticsuploads")
        for permission in permission:
            group.permissions.add(permission)
        permission = Permission.objects.filter(codename="view_logistics")
        for permission in permission:
            group.permissions.add(permission)
        group.save()
        group = Group(name='Budget')
        group.save()
        self.stdout.write(self.style.SUCCESS('Successfully created group'))