# backend/api/migrations/0009_remove_portfoliohistory_total_value_positive_and_more.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_portfoliohistory'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='portfoliohistory',
            name='total_value_positive',
        ),
        migrations.RemoveField(
            model_name='portfoliohistory',
            name='stock_breakdown',
        ),
        migrations.AlterField(
            model_name='portfoliohistory',
            name='total_value',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),
        migrations.AddConstraint(
            model_name='portfoliohistory',
            constraint=models.UniqueConstraint(fields=('user', 'date'), name='unique_portfolio_history_per_day'),
        ),
    ]
