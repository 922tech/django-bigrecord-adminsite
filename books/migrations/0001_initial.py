# Generated by Django 4.2.5 on 2023-09-18 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('publication_date', models.DateField()),
                ('price', models.FloatField()),
                ('no', models.CharField(max_length=20)),
                ('description', models.TextField()),
            ],
        ),
    ]
