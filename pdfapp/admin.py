from django.contrib import admin

from .models import PdfDetail, Invoice


# Register your models here.
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('tax_invoice_no', 'order_number', 'due_date', 'invoice_date', 'from_address', 'to_address',
                    'total_amount')


class InvoicepdfAdmin(admin.ModelAdmin):
    list_display = ('tax_invoice_no', 'client_pancard', 'client_name', 'project_code', 'total_amount',
                    'amount_in_words')


admin.site.register(PdfDetail, InvoiceAdmin)
admin.site.register(Invoice, InvoicepdfAdmin)
