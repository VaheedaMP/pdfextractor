# Generated by Django 5.0.3 on 2024-03-12 10:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pdfapp', '0004_alter_invoice_amount_in_words_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='invoice_date',
        ),
    ]
