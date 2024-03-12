import io
import os
from datetime import datetime

import PyPDF2
from rest_framework.decorators import api_view
from .models import PdfDetail, Invoice
from rest_framework import status
from rest_framework.response import Response
import fitz  # PyMuPDF
from django.http import JsonResponse
from .serializers import PdfDetailSerializer, InvoiceSerializer
from django.conf import settings
import pytesseract
from PIL import Image


# import logging
#
# logger = logging.getLogger(__name__)

def extract_img_text(filename):
    try:
        text = ''
        doc = fitz.open(filename)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_data = base_image["image"]
                image = Image.open(io.BytesIO(image_data))
                # Convert image to RGB format (PyMuPDF supports RGB images)
                if image.mode != "RGB":
                    image = image.convert("RGB")
                # Perform OCR on the image
                text += pytesseract.image_to_string(image)
        print(text)
        return text
    except Exception as e:
        print(f"Error occurred while extracting text from {filename}: {e}")
        return None


def extract_pdf_data(filename):
    try:
        text = ''
        with fitz.open(filename) as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
        return text
    except Exception as e:
        print("Error:", e)
        return None


def extract_invoice_data(text):
    parse_data = {"tax_invoice_no": "",
                  "client_pancard": "",
                  "client_name": "",
                  "project_code": "",
                  "total_amount": "",
                  "amount_in_words": "", }
    print(text)
    lines = text.splitlines()
    extract_dict = {}
    for line in lines:
        parts = line.split(":")
        if len(parts) == 2:
            extract_dict[parts[0].strip()] = parts[1].strip()
    print(extract_dict)
    for key, value in extract_dict.items():
        if "Invoice No".lower() in key.lower():
            parse_data["tax_invoice_no"] = value
        if "PAN" in key:
            parse_data["client_pancard"] = value
        if "Mr." in value:
            parse_data["client_name"] = value
        if "Project Code".lower() in key.lower():
            parse_data["project_code"] = value
        if "Total Amount".lower() in key.lower():
            parse_data["total_amount"] = value
        if "Amount in Words".lower() in key.lower():
            parse_data["amount_in_words"] = value
    print(parse_data)
    return parse_data


def parse_pdf_text(text):
    # Split the text into lines
    lines = text.split('\n')
    t = ("Order Number", "Invoice Number", "Invoice Date", "Due Date", "Total $", "From:", "To:", "Hrs/Qty", "Service")
    # Initialize variables to store extracted details
    tax_invoice_no = None
    order_number = None
    invoice_date = None
    due_date = None
    total_amount = None
    from_address = None
    to_address = None

    # Iterate through each line to extract details
    print("------------------------------------------------------", lines)
    for line in lines:
        line_lower = line.lower()  # Convert the line to lowercase
        if "invoice number".lower() in line_lower or "invoice no".lower() in line_lower or "invoice #".lower() in line_lower:
            tax_invoice_no = line.split("Invoice Number")[1].strip() if "Invoice Number".lower() in line_lower else \
                line.split("Invoice No")[1].strip() if "Invoice No".lower() in line_lower else \
                    line.split("Invoice #")[1].strip() if "Invoice #".lower() in line_lower else None
        elif "order number".lower() in line_lower:
            order_number = line.split("Order Number")[1].strip()
        elif "invoice date" in line_lower:
            invoice_date_str = line.split("Invoice Date")[1].strip()
            try:
                invoice_date = datetime.strptime(invoice_date_str, '%B %d, %Y').strftime('%Y-%m-%d')
            except ValueError:
                # Handle the case where the string cannot be parsed
                print("Error: Invalid date format")
        elif "due date" in line_lower:
            due_date_str = line.split("Due Date")[1].strip()
            try:
                due_date = datetime.strptime(due_date_str, '%B %d, %Y').strftime('%Y-%m-%d')
            except ValueError:
                # Handle the case where the string cannot be parsed
                print("Error: Invalid date format")
        elif "Total Due" in line_lower:  # Extract total amount
            total_amount_str = line.split("Total Due")[1].strip().replace('$', '')
            total_amount = float(total_amount_str)
            pass
        elif "from:" in line_lower:
            from_address_lines = []
            for i in range(lines.index(line) + 1, len(lines)):
                if any(lines[i].startswith(prefix) for prefix in t):
                    break
                from_address_lines.append(lines[i])
            from_address = "\n".join(from_address_lines)
        elif "to:" in line_lower:
            to_address_lines = []
            for i in range(lines.index(line) + 1, len(lines)):
                if any(lines[i].startswith(prefix) for prefix in t):
                    break
                to_address_lines.append(lines[i])
            to_address = "\n".join(to_address_lines)

        # Return a dictionary with the extracted details
    return {
        'tax_invoice_no': tax_invoice_no,
        'order_number': order_number,
        'invoice_date': invoice_date,
        'due_date': due_date,
        'total_due': total_amount,
        'from_address': from_address,
        'to_address': to_address,
    }


@api_view(['POST'])
def upload_pdf(request):
    if request.method == 'POST' and request.FILES['pdf_file']:
        pdf_file = request.FILES['pdf_file']
        file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)
        text = extract_pdf_data(file_path)
        parsed_data = parse_pdf_text(text)
        print("------------------------------------------------------------------", parsed_data)
        if 'tax_invoice_no' in parsed_data:
            invoice_number = parsed_data['tax_invoice_no']
            if PdfDetail.objects.filter(tax_invoice_no=invoice_number).exists():
                return JsonResponse({'error': 'Invoice with this number already exists.'}, status=400)

            serializer = PdfDetailSerializer(data=parsed_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Failed to extract invoice details from the PDF.' + text},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': 'Invalid request method or missing PDF file.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def upload_invoice_pdf(request):
    if request.method == 'POST' and request.FILES['pdf_file']:
        pdf_file = request.FILES['pdf_file']
        file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)
        text = extract_img_text(file_path)
        parsed_data = extract_invoice_data(text)
        if 'tax_invoice_no' in parsed_data:
            invoice_number = parsed_data['tax_invoice_no']
            if Invoice.objects.filter(tax_invoice_no=invoice_number).exists():
                return JsonResponse({'error': 'Invoice with this number already exists.'}, status=400)

            serializer = InvoiceSerializer(data=parsed_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Failed to extract invoice details from the PDF.' + text},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': 'Invalid request method or missing PDF file.'}, status=status.HTTP_400_BAD_REQUEST)
