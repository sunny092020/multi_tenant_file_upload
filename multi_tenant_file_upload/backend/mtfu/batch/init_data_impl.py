from mtfu.auth_user.models import Tenant
from django.db.models import Q


def copy_to_postgresql():
    create_tenants()


def create_tenants():
    for i in range(1, 11):
        username = "john" + str(i)
        
        # check if user exists
        if Tenant.objects.filter(Q(username=username)).exists():
            continue

        Tenant.create(
            username=username,
            password="test"
        )
