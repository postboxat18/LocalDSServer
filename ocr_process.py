import base64
import io
import json
import os
import pdfplumber
import subprocess
import sys
import time
from datetime import datetime

import easyocr
import fitz
import numpy as np
from PyPDF2 import PdfReader, PdfWriter

from PDF_editable import add_text_to_pdf
import pytesseract
from PIL import Image
from tqdm import tqdm

outputPath = os.getcwd()
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
gspath = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"
dpi = 300


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


def convert_pdf_to_images(rotate_pdf_path, logfile, clip_top_pixels=30):
    """Convert PDF pages to images."""
    try:
        doc = fitz.open(rotate_pdf_path)
    except Exception:
        log_exception("Error opening PDF", logfile)
        return []

    images = []

    # zoom = dpi / 72  # 300 DPI
    for i in tqdm(range(len(doc))):
        try:
            page = doc.load_page(i)

            # ZOOM
            pix_ori = page.get_pixmap()
            zoom_x = dpi / pix_ori.xres
            zoom_y = dpi / pix_ori.yres
            mat = fitz.Matrix(zoom_x, zoom_y)
            pix = page.get_pixmap(matrix=mat)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)

            img_clip_arr = img[clip_top_pixels:, :, :]

            # GET IMAGE SIZE
            width, height = pix.w, pix.h

            images.append({"image": img_clip_arr, "page_num": i + 1, "page_height": height,
                           "page_width": width, "x_res": pix_ori.xres,
                           "y_res": pix_ori.yres, })  # keep correct page num

        except Exception:
            log_exception(f"Error rendering page {i + 1}", logfile)

    doc.close()
    return images


def line_space_factor(all_coordinates, logfile):
    try:
        line_space_factor = []
        single_line = []
        ocr_text = []
        fin_ocr_text = []

        # CALCULATE SPACER
        for i, data in enumerate(all_coordinates):
            x0 = data["x0"]
            en_text = data["text"]
            w = data["width"]
            if x0 == 0.0:
                single_line = []
                ocr_text = []
            if en_text:
                text_len = len([i for i in en_text])
                text_space_factor = w // text_len
                single_line.append({"spfc": text_space_factor, "data": data})
                ocr_text.append(en_text)

            if i == len(all_coordinates) - 1 or all_coordinates[i + 1]["x0"] == 0.0:
                if single_line:

                    fin_ls = []
                    single_line = sorted(single_line, key=lambda x: x["spfc"])
                    # total = 0.0
                    for line in single_line:
                        #     total += line["spfc"]
                        fin_ls.append(line["data"])
                    # line_space_factor.append({"totalAvg": total / len(single_line), "single_line": fin_ls})
                    line_space_factor.append({"totalAvg": int(single_line[0]["spfc"]), "single_line": fin_ls})


                else:
                    line_space_factor.append({"totalAvg": 8, "single_line": [data]})
                # fin_ocr_text.append(ocr_text)
                # print(single_line,ocr_text)
        # ADD SPACER TEXT IN SINGLE LINE
        ocr_lines = []

        for i, data in enumerate(line_space_factor):
            space_factor = data["totalAvg"]
            isTrue = True
            while isTrue:
                try:
                    single_line_ls = data["single_line"]
                    items = [t for t in single_line_ls if t.get("text")]
                    if items:
                        # sort by x0
                        items.sort(key=lambda x: x["x0"])
                        line = ""
                        current_x = 0
                        y1_list = []
                        for item in items:
                            y1_list.append(item["y1"])
                            # print(item["x0"] - current_x)
                            gap = int((item["x0"] - current_x) / space_factor)  # convert coords to spaces
                            if gap > 0:
                                line += " " * gap
                            else:
                                line += " "
                            line += item["text"]
                            current_x = item["x1"]
                        # NEW LINE \N \N
                        y1_list = sorted(y1_list, key=lambda x: x, reverse=True)
                        new_line = "\n"
                        if not i == len(line_space_factor) - 1:
                            y0_list = [item["y0"] for item in line_space_factor[i + 1]["single_line"]]
                            y0_list = sorted(y0_list, key=lambda x: x)
                            y0 = y0_list[0]
                            y1 = y1_list[0]
                            y = y0 - y1
                            if y > 10:
                                new_line = "\n\n"
                        line += new_line
                        ocr_lines.append(line)
                    isTrue = False
                except Exception as e:
                    isTrue = True
                    space_factor -= 2
        return ocr_lines
    except Exception as e:
        log_exception("line_space_factor", logfile)
        return []


def default_space_factor(all_coordinates, page_width, logfile):
    try:
        # ADD SPACER TO TEXT
        space_factor = 8
        ocr_lines = []
        ocr_list_lines = []
        total_cols = int(page_width / space_factor)
        line_chars = []
        for i, data in enumerate(all_coordinates):
            x0 = data["x0"]
            en_text = data["text"]

            if x0 == 0:
                line_chars = []
                line_chars[0:total_cols] = [" "] * total_cols

            start_col = int(x0 / space_factor)

            if en_text:
                for k, ls in enumerate(range(start_col, start_col + len(en_text))):
                    line_chars[ls] = en_text[k]

            if i == len(all_coordinates) - 1:
                text = "".join(line_chars) + "\n"
                ocr_lines.append(text)
                ocr_list_lines.append(line_chars)
            elif all_coordinates[i + 1]["x0"] == 0:
                if len(line_chars) == total_cols:
                    text = "".join(line_chars) + "\n"
                    ocr_list_lines.append(line_chars)
                else:
                    n = total_cols - len(line_chars) - 1
                    line_chars[len(line_chars):total_cols] = [" "] * n
                    text = "".join(line_chars) + "\n"
                    ocr_list_lines.append(line_chars)
                ocr_lines.append(text)

        # REDUCE SPACER - 1. GET LETTER
        letter_list = []
        last_index = 0
        for ocr_list in ocr_list_lines:
            lt_lst = []
            for i, data in enumerate(ocr_list):
                last_index = i
                if data.strip():
                    lt_lst.append(i)
            if lt_lst:
                letter_list.extend(lt_lst)
        # REDUCE SPACER - 2. GET EMPTY DATA
        empty_lines = []
        for i in range(last_index):
            if not i in list(set(sorted(letter_list, key=lambda x: x))):
                empty_lines.append(i)

        empty_lines = sorted(empty_lines, key=lambda x: x)
        isTrue = True
        empty_range = []
        # REDUCE SPACER - 2. GET EMPTY RANGE
        for i, data in enumerate(empty_lines):
            if i == len(empty_lines) - 1:
                end = data
                empty_range.append(f'{start}-{end}')
            else:
                if isTrue:
                    start = data
                if empty_lines[i + 1] - data == 1:
                    isTrue = False
                else:
                    isTrue = True
                    end = data
                if isTrue:
                    empty_range.append(f'{start}-{end}')
        # REDUCE SPACER - 3. REMOVE SPACER IN INDEX
        empty_range = sorted(empty_range, key=lambda x: x, reverse=True)
        new_lines = []
        for ocr_lines in ocr_list_lines:
            len_ocr = len(ocr_lines)
            line_chars = []
            for i in range(len_ocr):
                isSpace = True
                for rng in empty_range:
                    spl = rng.split("-")
                    start = int(spl[0])
                    end = int(spl[1])
                    if end - start > 5:
                        if i in [r for r in range(start, end)]:
                            isSpace = False
                            if start + 1 == i:
                                line_chars.append(" ")

                if ocr_lines[i].strip() or isSpace:
                    line_chars.append(ocr_lines[i])
            text = "".join(line_chars) + "\n"
            new_lines.append(text)

        return new_lines
    except Exception as e:
        log_exception("default_space_factor", logfile)
        return []


def Text_easr_ocr(image, page_num, page_height, page_width, x_res, y_res, reader, logfile):
    try:
        result = reader.readtext(
            image,
            output_format="dict",
            canvas_size=3860,
            height_ths=0.7,
            width_ths=0.9, )
        if result:
            # GET RESPONSE
            all_res = []
            for i, entry in enumerate(result):
                en_text = entry['text'].strip()
                bbox = entry['boxes']
                score_ = float(entry["confident"])
                x0 = float(bbox[0][0])
                y0 = float(bbox[0][1]) + 30
                x1 = float(bbox[2][0])
                y1 = float(bbox[2][1]) + 30
                all_res.append({"x0": x0,
                                "y0": y0,
                                "x1": x1,
                                "y1": y1,
                                'width': int(x1 - x0),
                                'height': int(y1 - y0),
                                'text': en_text,
                                'Page': page_num,
                                'confident_score': score_})
            try:
                with open(os.path.join(outputPath, "outExtr_pages.json"), "w+") as f:
                    json.dump(all_res, f, indent=4)
                # ADD BLANK TEXT FOR GIVEN COORDINATES
                all_res = sorted(all_res, key=lambda x: x["y0"])
                all_coordinates = []
                for i, data in enumerate(all_res):
                    x0 = data["x0"]
                    y0 = data["y0"]
                    x1 = data["x1"]
                    y1 = data["y1"]
                    en_text = data["text"]

                    last_y0 = y0 - float(all_res[i - 1]["y0"])

                    if not i == 0:
                        last_y0 = y0 - float(all_res[i - 1]["y0"])
                        last_x1 = float(all_res[i - 1]["x1"])

                        if last_y0 > 10:
                            x1_ = float(all_res[i - 1]["x1"])
                            all_coordinates.append({
                                "x0": x1_,
                                "y0": y0,
                                "x1": page_width,
                                "y1": y1,
                                'width': int(page_width - x1_),
                                'height': int(y1 - y0),
                                'text': "",
                                'Page': data["Page"],
                                'confident_score': 0
                            })

                            all_coordinates.append({
                                "x0": 0,
                                "y0": y0,
                                "x1": x0,
                                "y1": y1,
                                'width': int(x0),
                                'height': int(y1 - y0),
                                'text': "",
                                'Page': data["Page"],
                                'confident_score': 0
                            })
                            all_coordinates.append({
                                "x0": x0,
                                "y0": y0,
                                "x1": x1,
                                "y1": y1,
                                'width': int(x1 - x0),
                                'height': int(y1 - y0),
                                'text': en_text,
                                'Page': data["Page"],
                                'confident_score': data["confident_score"]
                            })
                        else:

                            x1_ = float(all_res[i - 1]["x1"])
                            if x0 > x1_:
                                all_coordinates.append({
                                    "x0": x1_,
                                    "y0": y0,
                                    "x1": x0,
                                    "y1": y1,
                                    'width': int(x0 - x1_),
                                    'height': int(y1 - y0),
                                    'text': "",
                                    'Page': data["Page"],
                                    'confident_score': 0
                                })

                            all_coordinates.append({
                                "x0": x0,
                                "y0": y0,
                                "x1": x1,
                                "y1": y1,
                                'width': int(x1 - x0),
                                'height': int(y1 - y0),
                                'text': en_text,
                                'Page': data["Page"],
                                'confident_score': data["confident_score"]
                            })
                    else:

                        all_coordinates.append({
                            "x0": 0,
                            "y0": y0,
                            "x1": x0,
                            "y1": y1,
                            'width': int(x0),
                            'height': int(y1 - y0),
                            'text': "",
                            'Page': data["Page"],
                            'confident_score': 0
                        })
                        all_coordinates.append({
                            "x0": x0,
                            "y0": y0,
                            "x1": x1,
                            "y1": y1,
                            'width': int(x1 - x0),
                            'height': int(y1 - y0),
                            'text': en_text,
                            'Page': data["Page"],
                            'confident_score': data["confident_score"]
                        })

                ocr_lines = default_space_factor(all_coordinates, page_width, logfile)
                # ocr_lines = line_space_factor(all_coordinates, logfile)
                # #ADD MULTIPLE DPI FOR COORDINATES
                coordinates = []
                for i, data in enumerate(all_coordinates):
                    x0 = data["x0"]
                    y0 = data["y0"]
                    x1 = data["x1"]
                    y1 = data["y1"]
                    x0_ = x0 * x_res / dpi
                    y0_ = y0 * y_res / dpi
                    x1_ = x1 * x_res / dpi
                    y1_ = y1 * y_res / dpi
                    data["x0"] = x0_
                    data["y0"] = y0_
                    data["x1"] = x1_
                    data["y1"] = y1_
                    data["width"] = int(x1_ - x0_)
                    data["height"] = int(y1_ - y0_)
                    coordinates.append(data)
                return ocr_lines, coordinates

            except Exception as e:
                log_exception("text_easr_ocr_1:", logfile)
                with open(os.path.join(outputPath, "outExtr_5pages.json"), "w+") as f:
                    json.dump(all_res, f, indent=4)
                return [""], [{"x0": 0,
                               "y0": 0,
                               "x1": 0,
                               "y1": 0,
                               'width': page_width,
                               'height': page_height,
                               'text': "",
                               'Page': page_num,
                               'confident_score': 0}]
        else:
            return [""], [{"x0": 0,
                           "y0": 0,
                           "x1": 0,
                           "y1": 0,
                           'width': page_width,
                           'height': page_height,
                           'text': "",
                           'Page': page_num,
                           'confident_score': 0}]
    except Exception:
        log_exception("Error IN EASY OCR", logfile)
        return [""], [{"x0": 0,
                       "y0": 0,
                       "x1": 0,
                       "y1": 0,
                       'width': page_width,
                       'height': page_height,
                       'text': "",
                       'Page': page_num,
                       'confident_score': 0}]


def run_ocr(image_paths, log_file):
    return_list = []
    reader = easyocr.Reader(['en'], gpu=True)
    for num, img_path_ in enumerate(tqdm(image_paths)):
        try:
            img_path = img_path_["image"]
            page_num = img_path_["page_num"]
            page_height = img_path_["page_height"]
            page_width = img_path_["page_width"]
            x_res = img_path_["x_res"]
            y_res = img_path_["y_res"]
            results, coordinates = Text_easr_ocr(img_path, num + 1, page_height, page_width, x_res, y_res, reader,
                                                 log_file)
            texts = " ".join(results)
            texts = texts.replace(' - ', '-')
            texts = texts.replace('\"', '\'')
            return_list.append({page_num + 1: {"text": texts, "coordinates": coordinates}})
        except Exception as e:
            log_exception("Error IN EASY OCR", log_file)
    return return_list


def rotateFunc(input_pdf_path, rotation_pdf_path, log_file, dpi=dpi, ):
    try:
        doc = fitz.open(input_pdf_path)
        for i in tqdm(range(len(doc))):
            try:
                page = doc.load_page(i)
                page.set_rotation(0)

                pix_ori = page.get_pixmap()
                zoom_x = dpi / pix_ori.xres
                zoom_y = dpi / pix_ori.yres
                mat = fitz.Matrix(zoom_x, zoom_y)
                pix = page.get_pixmap(matrix=mat)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                image_arr = Image.fromarray(img)

                orientation = pytesseract.image_to_osd(image_arr, config="--psm 0 -c min_characters_to_try=15",
                                                       output_type='dict')
                if orientation["orientation_conf"] > 2.0:
                    to_rotate = orientation["rotate"]
                    # ROTATE
                    page.set_rotation(to_rotate)

            except Exception as e:
                log_exception("rotateFunc:inside:", log_file)
        doc.save(rotation_pdf_path)
        doc.close()
    except Exception as e:
        log_exception("rotateFunc", log_file)


def wordCordinates(pdf_file_path, logfile):
    try:
        words_coordinates = []
        with pdfplumber.open(pdf_file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words()
                height, width = page.height, page.width

                for word in words:
                    words_coordinates.append({
                        "text": word["text"],
                        "Page": page_num + 1,
                        "x0": word["x0"],
                        "y0": word["top"],
                        "x1": word["x1"],
                        "y1": word["bottom"],
                        "height": height,
                        "width": width
                    })

        return words_coordinates

    except Exception as e:
        log_exception("In app.py wordCordinates", logfile)


def ocr_text(rotate_pdf_path, logfile):
    try:
        all_text = []
        word_coordinates = []
        doc = fitz.open(rotate_pdf_path)
        for i in tqdm(range(len(doc))):
            try:
                page = doc.load_page(i)
                page.set_rotation(0)

                pix_ori = page.get_pixmap()
                zoom_x = dpi / pix_ori.xres
                zoom_y = dpi / pix_ori.yres
                mat = fitz.Matrix(zoom_x, zoom_y)
                pix = page.get_pixmap(matrix=mat)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                image_arr = Image.fromarray(img)

                text = pytesseract.image_to_string(image_arr, config="--psm 6 -c min_characters_to_try=15")
                all_text.append(text)
            except:
                log_exception("ocr_Text loop:", logfile)
        word_coordinates = wordCordinates(rotate_pdf_path, logfile)
        return all_text, word_coordinates
    except:
        log_exception("ocr_Text:", logfile)


def Easyocr_text(rotate_pdf_path, logfile):
    try:

        image_paths = convert_pdf_to_images(rotate_pdf_path, logfile)
        extracted_texts = run_ocr(image_paths, logfile)
        sorted_by_key = sorted(extracted_texts, key=lambda d: list(d.keys())[0])
        # pdf_all_texts = [list(a.values())[0] for a in sorted_by_key]
        pdf_all_texts = [{"text": list(a.values())[0]["text"], "coordinates": list(a.values())[0]["coordinates"], } for
                         a in sorted_by_key]
        return pdf_all_texts
    except Exception as e:
        log_exception("EASY OCR TEXT", logfile)
        return []


def wait_for_pdf_ready(filepath, len_path, timeout=10):
    """Wait until PDF is ready to read."""
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(filepath) and len(fitz.open(filepath)) == len_path:
            try:
                fitz.open(filepath)
                return True
            except:
                pass
        time.sleep(0.2)
    return False


def wait_for_pdf_ready1(filepath, timeout=10):
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


def remove_annotations(input_pdf, output_path, logfile):
    try:
        doc = fitz.open(input_pdf)
        new_doc = fitz.open()
        for i in range(len(doc)):
            page = doc.load_page(i)
            # Render page to image
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")

            # Create new PDF page same size as original
            rect = page.rect
            new_page = new_doc.new_page(width=rect.width, height=rect.height)

            # Insert the image
            new_page.insert_image(rect, stream=img_bytes)

        new_doc.save(output_path)
        new_doc.close()
        doc.close()


    except Exception as e:
        log_exception("In OCR Module remove_annotations", logfile)


def compress_file(output_path, img_pdf_path, logfile):
    try:
        args = [
            gspath,
            '-dCompatibilityLevel=1.4',
            '-sDEVICE=pdfwrite',
            '-dShowAnnots=false',
            '-dShowAcroForm=false',
            "-dPDFSETTINGS=/ebook",
            '-dFastWebView=true',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={img_pdf_path}',
            output_path
        ]

        # Execute Ghostscript command
        process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode != 0:
            log_exception("Ghostscript failed:compress_file", logfile)
            return False
        return True

    except Exception as e:
        log_exception("compress_file", logfile)


def ocr_method(method, base64File, format, logfile):
    try:
        base_Coder = base64.b64decode(base64File)

        input_pdf_path = ""
        if format == "image":
            try:
                img = Image.open(io.BytesIO(base_Coder))
                imgPath = os.path.join(outputPath, "imgPath")
                if not os.path.exists(imgPath):
                    os.mkdir(imgPath)
                # with open(os.path.join(imgPath, f"img.{img.format}"), "wb") as f:
                #     f.write(base_Coder)
                input_pdf_path = os.path.join(imgPath, "sample_repaired.pdf")
                img.save(input_pdf_path)
            except:
                log_exception("easyocr_process:", logfile)
        elif format == "pdf":
            try:
                pdfPath = os.path.join(outputPath, "pdfPath")
                if not os.path.exists(pdfPath):
                    os.mkdir(pdfPath)

                pdf_filePath = os.path.join(pdfPath, "sample.pdf")
                input_pdf_path = os.path.join(pdfPath, "sample_repaired.pdf")
                with open(pdf_filePath, 'wb') as f:
                    f.write(base_Coder)
                reader = PdfReader(pdf_filePath)
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)

                with open(input_pdf_path, "wb") as f:
                    writer.write(f)

            except:
                log_exception("easyocr_process:", logfile)
        else:
            input_pdf_path = ""
        if input_pdf_path:
            split_path = os.path.split(input_pdf_path)
            rotate_pdf_path = os.path.join(split_path[0], f"rotate_{split_path[1]}")

            if not wait_for_pdf_ready1(input_pdf_path):
                log_exception("PDF not ready for OCR", logfile)
                return []
            rotateFunc(input_pdf_path, rotate_pdf_path, logfile, dpi)
            if not wait_for_pdf_ready(rotate_pdf_path, len(fitz.open(input_pdf_path))):
                log_exception("PDF not ready for OCR", logfile)
                return []
            if method == "easyocr":
                all_res = Easyocr_text(rotate_pdf_path, logfile)
                coordinates = []
                all_text = []
                if all_res:
                    for i, data in enumerate(all_res):
                        all_text.append(data["text"])
                        coordinates.append(data["coordinates"])
            else:
                all_text, coordinates = ocr_text(rotate_pdf_path, logfile)

            annot_pdf_path = os.path.join(split_path[0], f"annot_{split_path[1]}")
            remove_annotations(rotate_pdf_path, annot_pdf_path, logfile)

            compress_pdf_path = os.path.join(split_path[0], f"comp_{split_path[1]}")
            compress_file(annot_pdf_path, compress_pdf_path, logfile)
            if not wait_for_pdf_ready(compress_pdf_path, len(fitz.open(input_pdf_path))):
                log_exception("PDF not ready for OCR", logfile)
                return []
            output_pdf_path = os.path.join(split_path[0], f"converted_{split_path[1]}")
            # RE - EDIT
            if method == "easyocr":
                add_text_to_pdf(compress_pdf_path, output_pdf_path, coordinates, logfile)
            # REMOVE PATH
            if os.path.isfile(input_pdf_path):
                os.remove(input_pdf_path)

            if os.path.isfile(rotate_pdf_path):
                os.remove(rotate_pdf_path)

            if os.path.isfile(compress_pdf_path):
                os.remove(compress_pdf_path)

            if os.path.isfile(annot_pdf_path):
                os.remove(annot_pdf_path)

            return {
                "texts": all_text,
                "coordinates": coordinates,
                "output_path": output_pdf_path,
                "total_pages": len(all_text),
            }
        else:
            return {
                "texts": "",
                "coordinates": "",
                "output_path": "",
                "total_pages": 0,
            }
    except:
        log_exception("ocr_method", logfile)
