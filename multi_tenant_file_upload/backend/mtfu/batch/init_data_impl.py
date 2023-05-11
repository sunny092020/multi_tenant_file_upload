from mtfu.auth_user.models import Tenant
from django.db.models import Q
from bulk_sync import bulk_sync


def copy_to_postgresql():
    print("Copying data to PostgreSQL")
    create_tenants()


def create_tenants():
    users = []

    for i in range(1, 11):
        user = Tenant(username="john" + str(i))
        user.set_password("mypassword")
        users.append(user)

    filters = Q()
    key_fields = ("username",)
    ret = bulk_sync(
        new_models=users,
        filters=filters,
        key_fields=key_fields,
        skip_deletes=True,
        skip_updates=False,
    )

    print(
        "Results of bulk_sync users: " "{created} created, {updated} updated, {deleted} deleted.".format(**ret["stats"])
    )
