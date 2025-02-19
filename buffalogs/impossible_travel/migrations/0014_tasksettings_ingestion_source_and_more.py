# Generated by Django 4.2.16 on 2025-02-19 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("impossible_travel", "0013_remove_alert_valid_alert_name_choice_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tasksettings",
            name="ingestion_source",
            field=models.CharField(
                choices=[("elasticsearch", "Data Ingestion from Elasticsearch")],
                default="elasticsearch",
                max_length=30,
            ),
        ),
        migrations.AddConstraint(
            model_name="tasksettings",
            constraint=models.CheckConstraint(
                check=models.Q(("ingestion_source__in", ["elasticsearch"])),
                name="valid_ingestion_source_choice",
            ),
        ),
    ]
