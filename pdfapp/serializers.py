from rest_framework import serializers
from .models import PdfDetail


class PdfDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdfDetail
        fields = ['tax_invoice_no', 'order_number', 'due_date', 'invoice_date', 'from_address', 'to_address',
                  'total_amount']
