import io
import os
import sys
import time
from datetime import datetime

import fitz
import numpy as np
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from tqdm import tqdm


def log_exception(func_name, logfile):
    exc_type, exc_obj, tb = sys.exc_info()
    lineno = tb.tb_lineno
    error_message = f"\nIn {func_name} LINE.NO-{lineno} : {exc_obj}"
    print("error_message : ", error_message)
    with open(logfile, 'a', encoding='utf-8') as fp:
        fp.writelines(error_message)


def process_logger(process, logfile):
    with open(logfile, 'a', encoding='utf-8') as fp:
        fp.writelines(f'\n{datetime.now()} {process}')


# ---------------------------------------------- PYTESSERACT---------------------------------------------------->
dpi = 300
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"
gspath = r"/usr/bin/gs"


def pytesseract_text(input_pdf_path, log_file, dpi=dpi, ):
    try:
        doc = fitz.open(input_pdf_path)
        all_res = []
        for i in tqdm(range(len(doc))):
            try:
                page = doc.load_page(i)
                page.set_rotation(0)

                pix_ori_ = page.get_pixmap()
                zoom_x_ = dpi / pix_ori_.xres
                zoom_y_ = dpi / pix_ori_.yres
                mat_ = fitz.Matrix(zoom_x_, zoom_y_)
                pix_ = page.get_pixmap(matrix=mat_)
                img_ = np.frombuffer(pix_.samples, dtype=np.uint8).reshape(pix_.h, pix_.w, pix_.n)
                image_arr_ = Image.fromarray(img_)

                orientation = pytesseract.image_to_osd(image_arr_, config="--psm 0 -c min_characters_to_try=15",
                                                       output_type='dict')
                # ROTATE PAGE
                to_rotate = orientation["rotate"]
                # ROTATE
                page.set_rotation(to_rotate)

                # NOW EXTRACT TEXT FROM PYTESSERACT
                pix_ori = page.get_pixmap()
                zoom_x = dpi / pix_ori.xres
                zoom_y = dpi / pix_ori.yres
                mat = fitz.Matrix(zoom_x, zoom_y)
                pix = page.get_pixmap(matrix=mat)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                image_arr = Image.fromarray(img)
                text = pytesseract.image_to_string(image_arr, config='--psm 3')
                all_res.append({"text": text, "page_num": i + 1, "coordinates": ""})
            except Exception as e:
                log_exception("rotateFunc:inside:", log_file)
        return all_res
    except Exception as e:
        log_exception("rotateFunc", log_file)
        return []


def pytesseract_ocr(pdf_path, logfile):
    try:
        all_res = pytesseract_text(pdf_path, logfile, dpi)
        return all_res
    except:
        log_exception("pytesseract_ocr:", logfile)
        return []


# ---------------------------------------------- MAKE EDITABLE PDF ---------------------------------------------------->
def wait_for_pdf_ready(filepath, timeout=10):
    """Wait until PDF is ready to read."""
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            try:
                fitz.open(filepath)
                return True
            except:
                pass
        time.sleep(0.2)
    return False


def page_size(pdf_file, page_number):
    doc = fitz.open(pdf_file)
    page = doc[page_number]
    width = page.rect.width
    height = page.rect.height
    return width, height


def page_over_write(rotate_pdf_path, page_num, image_coordinates, page_, page_text, preprocess_images, logfile):
    try:
        page_number = page_num - 1
        # if page_text < 100:
        page_width, page_height = page_size(rotate_pdf_path, page_number)

        # img_width = float(image_coordinates[page_number][1])
        # img_height = float(image_coordinates[page_number][2])

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height), bottomup=True)
        can.setFillColor(Color(0, 0, 0, alpha=0))

        for cord in image_coordinates[page_num - 1]:
            x = cord["x0"]
            y = page_height - cord["y1"]
            h = cord['height']
            w = cord['width']
            text = cord["text"]
            if text:
                font_name = "Helvetica"
                face = pdfmetrics.getFont(font_name).face
                descent = (face.descent / 1000.0) * h

                # Measure text width at this font size
                text_width = pdfmetrics.stringWidth(text, font_name, h)

                # Calculate horizontal scaling factor to fit within box width
                scale_x = w / text_width if text_width > 0 else 1.0

                # Apply scaling (only horizontal stretch/shrink)
                can.saveState()
                can.translate(x, y - descent)  # move origin to text start
                can.scale(scale_x, 1.0)  # compress/expand in X
                can.setFont(font_name, h)
                can.drawString(0, 0, text)  # draw at new scaled origin
                can.restoreState()

                # can.rect(x=cord["x0"], y=y, height=cord["height"], width=cord["width"], fill=1)

        can.save()
        packet.seek(0)
        new_pdf = PdfReader(packet)
        new_pdf_page = new_pdf.pages[0]

        rotation_1 = new_pdf_page.get('/Rotate')
        rotation_2 = page_.get('/Rotate')

        if rotation_2 == 90 or rotation_2 == 270 or rotation_2 == 180:
            new_pdf_page.rotate(-rotation_2)
            new_pdf_page.transfer_rotation_to_content()

        page_.merge_page(new_pdf_page)
        page_.compress_content_streams()
        preprocess_images.append({page_num: page_})

    except Exception as e:
        log_exception("In OCR Module add_text_to_pdf", logfile)


def add_text_to_pdf(rotate_pdf_path, output_pdf_path, image_coordinates, logfile):
    try:
        # process_logger("In OCR Module add_text_to_pdf", logfile)
        pdf_writer = PdfWriter()  # Create a new PDF writer
        preprocess_images = []  # List to store modified pages

        pdf_reader = PdfReader(rotate_pdf_path, strict=False)  # Read the default PDF

        # Iterate through each page of the existing PDF
        for page_number in range(len(pdf_reader.pages)):
            page_ = pdf_reader.pages[page_number]
            page_text = len(page_.extract_text().split())

            # Process each page without threading
            page_over_write(rotate_pdf_path, page_number + 1, image_coordinates, page_, page_text, preprocess_images,
                            logfile)

        # Arrange pages in the correct order
        gp_pages = sorted(preprocess_images, key=lambda x: list(x.keys())[0])  # Arrange page format
        for i, page_opt_ in enumerate(gp_pages):
            page_opt = list(dict(page_opt_).values())[0]
            pdf_writer.add_page(page_opt)

        # Write the result to the output PDF file
        with open(output_pdf_path, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
            return "Successfully Converted"


    except Exception as e:
        pdf_writer = PdfWriter()  # Create a new PDF writer
        preprocess_images = []  # List to store modified pages
        error_message = str(e)
        if "incorrect startxref pointer(1)" in error_message.lower():
            pdf_reader = PdfReader(rotate_pdf_path, strict=False)  # Read the default PDF

            # Iterate through each page of the existing PDF
            for page_number in range(len(pdf_reader.pages)):
                page_ = pdf_reader.pages[page_number]
                page_text = len(page_.extract_text().split())

                # Process each page without threading
                page_over_write(rotate_pdf_path, page_number + 1, image_coordinates, page_, page_text,
                                preprocess_images,
                                logfile)

            # Arrange pages in the correct order
            gp_pages = sorted(preprocess_images, key=lambda x: list(x.keys())[0])  # Arrange page format
            for i, page_opt_ in enumerate(gp_pages):
                page_opt = list(dict(page_opt_).values())[0]
                pdf_writer.add_page(page_opt)

            # Write the result to the output PDF file
            with open(output_pdf_path, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)
                return "Successfully Converted"

        log_exception("In OCR Module add_text_to_pdf", logfile)
        print("Error in adding text to PDF", error_message)
        return "Error in adding text to PDF"

