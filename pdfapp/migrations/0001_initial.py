# Generated by Django 5.0.3 on 2024-03-11 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PdfDetail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=255)),
                ('tax_invoice_no', models.CharField(blank=True, max_length=255, unique=True)),
                ('status', models.CharField(choices=[('PROCESSING', 'Processing'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')], default='PROCESSING', max_length=50)),
            ],
        ),
    ]
