from django.core.management.base import BaseCommand
from core.models import *
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **kwargs):
        Answer.objects.all().delete()
        Form.objects.all().delete()