from rest_framework import serializers
from .models import PdfDetail, Invoice


class PdfDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdfDetail
        fields = ['tax_invoice_no', 'order_number', 'due_date', 'invoice_date', 'from_address', 'to_address',
                  'total_amount']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['tax_invoice_no', 'client_pancard', 'client_name', 'project_code', 'total_amount',
                  'amount_in_words']
