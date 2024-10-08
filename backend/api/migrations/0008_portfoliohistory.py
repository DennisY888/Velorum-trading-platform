# Generated by Django 5.1 on 2024-09-10 07:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_history_api_history_user_id_5d7cc4_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortfolioHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('total_value', models.DecimalField(decimal_places=2, max_digits=20)),
                ('stock_breakdown', models.JSONField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_history', to='api.userprofile')),
            ],
            options={
                'ordering': ['-date'],
                'constraints': [models.CheckConstraint(condition=models.Q(('total_value__gte', 0)), name='total_value_positive')],
            },
        ),
    ]
