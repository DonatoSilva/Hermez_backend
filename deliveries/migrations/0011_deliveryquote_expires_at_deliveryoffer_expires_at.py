from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deliveries', '0010_deliveryquote_vehicle_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryoffer',
            name='expires_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='deliveryquote',
            name='expires_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
