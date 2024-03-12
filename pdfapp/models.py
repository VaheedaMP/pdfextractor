from django.db import models

# Create your models here.


class PdfDetail(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    filename = models.CharField(max_length=255)
    tax_invoice_no = models.CharField(max_length=255,unique=True, blank=True)
    order_number = models.CharField(max_length=100, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    invoice_date = models.DateField(blank=True, null=True)
    from_address = models.TextField(blank=True, null=True)
    to_address = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=50, choices=[
        ('PROCESSING', 'Processing'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ], default='PROCESSING')  # Default status

    def __str__(self):
        return self.filename

    def save_from_json(self, data):
        self.filename = data.get('filename', '')  # Handle potential missing filename
        self.tax_invoice_no = data.get('tax_invoice_no', '')
        self.save()
class Invoice(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    tax_invoice_no = models.CharField(max_length=50,unique=True, blank=True)
    invoice_date = models.DateField(blank=True, null=True)
    client_pancard = models.CharField(max_length=20,blank=True, null=True)
    client_name = models.CharField(max_length=100,blank=True, null=True)
    project_code = models.CharField(max_length=20,blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    amount_in_words = models.CharField(max_length=200,blank=True, null=True)