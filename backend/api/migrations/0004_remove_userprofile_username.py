# backend/api/migrations/0004_remove_userprofile_username.py

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_watchlist'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='username',
        ),
    ]
