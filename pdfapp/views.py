import json
import os
from datetime import datetime

import PyPDF2
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import re
from PyPDF2 import PdfReader
import logging

from rest_framework.decorators import api_view

from .models import PdfDetail
from django.db.utils import IntegrityError
import logging.config
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import fitz  # PyMuPDF
import pdfplumber

# Configure logging using the configuration file
# logging.config.fileConfig('logging.conf')

# Get the logger for this module
# from pdfexactor.log_config import setup_logger
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .serializers import PdfDetailSerializer
from django.conf import settings



# Setup your logger
# logger = setup_logger('pdf_extraction', 'logs/pdf_extraction.log')

def extract_pdf_data(file_path):
    # with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file_path)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
        print(text)
        return text
# def extract_pdf_data(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
#
#     if 'pdf_file' not in request.FILES:
#         return JsonResponse({'error': 'Missing pdf_file field in request body'}, status=400)
#
#     pdf_file = request.FILES['pdf_file']
#     tax_invoice_no = ""
#
#     try:
#         pdf_reader = PdfReader(pdf_file)
#         print('Successfully opened uploaded PDF file.')
#
#         for page_num in range(len(pdf_reader.pages)):
#             page = pdf_reader.pages[page_num]
#             page_text = page.extract_text()
#             tax_invoice_pattern = r"""
#             (?:
#                 Tax\s+Invoice\s+No\s[:].|  # Tax Invoice No. (with optional space)
#                 Tax\s+Invoice\s*[:],    # Tax Invoice: (with optional space and comma)
#                 Invoice\s+No\.|          # Invoice No.
#                 Invoice\s*[:]            # Invoice: (with optional space and colon)
#             )\s*
#             (\w+\s*\d+)              # Capture alphanumeric + digits (including spaces)
#         """
#
#             match = re.search(tax_invoice_pattern, page_text, re.IGNORECASE | re.VERBOSE)
#
#             if match:
#                 tax_invoice_no = match.group(1).strip()
#                 print(f'Extracted tax invoice number: {tax_invoice_no}')
#
#         try:
#             pdf_detail = PdfDetail(filename=request.FILES['pdf_file'].name, tax_invoice_no=tax_invoice_no)
#             pdf_detail.save()
#             return JsonResponse({'tax_invoice_no': tax_invoice_no})  # Success, return tax invoice number
#         except IntegrityError:
#             print(f'Duplicate tax invoice number: {tax_invoice_no}')
#             return JsonResponse({'tax_invoice_no': 'Duplicate tax invoice number found.'},
#                                 status=409)  # Conflict (duplicate)
#
#     except Exception as e:
#         print(f'Error processing PDF: {str(e)}')
#         return JsonResponse({'error': f'Error processing PDF: {str(e)}'}, status=500)
#
#
# @csrf_exempt
# def extract_pdf_view(request):
#     """
#     Wrapper view for handling CSRF exemption for the extract_pdf_data function.
#     """
#     return extract_pdf_data(request)


def parse_pdf_text(text):
    # Split the text into lines
    lines = text.split('\n')

    # Initialize variables to store extracted details
    tax_invoice_no = None
    order_number = None
    invoice_date = None
    due_date = None
    total_amount = None
    from_address = None
    to_address = None

    # Iterate through each line to extract details
    for line in lines:
        if "Invoice Number" in line:
            tax_invoice_no = line.split("Invoice Number")[1].strip()
        elif "Order Number" in line:
            order_number = line.split("Order Number")[1].strip()
        elif "Invoice Date" in line:
            invoice_date_str = line.split("Invoice Date")[1].strip()
            invoice_date = datetime.strptime(invoice_date_str, '%B %d, %Y').strftime('%Y-%m-%d')
        elif "Due Date" in line:
            due_date_str = line.split("Due Date")[1].strip()
            due_date = datetime.strptime(due_date_str, '%B %d, %Y').strftime('%Y-%m-%d')
        elif "Total $" in line:  # Extract total amount
            total_amount = float(line.split("Total $")[1].strip())
        elif "From:" in line:
            try:
                from_address_lines = lines[lines.index(line) + 1: lines.index("To:")]
                from_address = "\n".join(line for line in from_address_lines if '@' not in line)  # Exclude email
            except ValueError:
                pass
        elif "To:" in line:
            try:
                to_address_lines = lines[lines.index(line) + 1: lines.index("Hrs/Qty")]
                to_address = "\n".join(line for line in to_address_lines if '@' not in line)  # Exclude email
            except ValueError:
                to_address = "\n".join(lines[lines.index(line) + 1:])
                break

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
        # file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.name)
        # with open(file_path, 'wb') as destination:
        #     for chunk in pdf_file.chunks():
        #         destination.write(chunk)
        text = extract_pdf_data(pdf_file)
        print(text)
        parsed_data = parse_pdf_text(text)
        if 'tax_invoice_no' in parsed_data:
            invoice_number = parsed_data['tax_invoice_no']
            if PdfDetail.objects.filter(tax_invoice_no=invoice_number).exists():
                return JsonResponse({'error': 'Invoice with this number already exists.'}, status=400)

            serializer = PdfDetailSerializer(data=parsed_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Failed to extract invoice details from the PDF.'+text},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': 'Invalid request method or missing PDF file.'}, status=status.HTTP_400_BAD_REQUEST)
