from django.contrib import admin

from .models import PdfDetail


# Register your models here.
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('tax_invoice_no', 'order_number', 'due_date', 'invoice_date', 'from_address', 'to_address',
                  'total_amount')


admin.site.register(PdfDetail, InvoiceAdmin)
