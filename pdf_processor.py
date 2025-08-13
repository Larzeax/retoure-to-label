import io
import os
import datetime
import sys
import PyPDF2
import pdfrw
import requests
from readConfig import discordWebhook, openFiles
import fitz  # PyMuPDF
from PIL import Image

def check_private(file_buffer):
    file = PyPDF2.PdfReader(file_buffer)
    searchItems = ["Warenkorb-Nr", "Privat"]
    for page in file.pages:
        text = page.extract_text()
        if any(item in text for item in searchItems):
            return True
    return False


def check_retoure(file_buffer):
    file = PyPDF2.PdfReader(file_buffer)
    searchItems = ["Rücksendeetikett", "Rücksendezentrum", "Returns Centre"]
    for page in file.pages:
        text = page.extract_text()
        if any(item in text for item in searchItems):
            return True
    return False


def extract_and_rotate_images(file_buffer):
    doc = fitz.open(stream=file_buffer.read(), filetype="pdf")
    pdf_writer = PyPDF2.PdfWriter()

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            image = Image.open(io.BytesIO(doc.extract_image(img[0])["image"]))
            rotated_image = image.rotate(270, expand=True)

            img_byte_arr = io.BytesIO()
            rotated_image.save(img_byte_arr, format='PDF')
            img_byte_arr.seek(0)

            pdf_image = PyPDF2.PdfReader(img_byte_arr)
            pdf_writer.add_page(pdf_image.pages[0])

    doc.close()

    output_buffer = io.BytesIO()
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer


def split_and_rotate(file_buffer):
    file_buffer.seek(0)
    writer = pdfrw.PdfWriter()
    reader = pdfrw.PdfReader(fdata=file_buffer.read())

    for page in reader.pages:
        newpage = pdfrw.PageMerge()
        newpage.add(page, viewrect=(0, 0, 1, 0.5))
        page = newpage.render()
        page.Rotate = 90
        writer.addpage(page)

    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer


def concatenate_buffers(pdf_buffers):
    writer = pdfrw.PdfWriter()

    for buffer in pdf_buffers:
        buffer.seek(0)
        reader = pdfrw.PdfReader(fdata=buffer.read())
        writer.addpages(reader.pages)

    merged_buffer = io.BytesIO()
    writer.write(merged_buffer)
    merged_buffer.seek(0)
    return merged_buffer


def crop_pdf_to_format(pdf_buffer):
    def mm_to_points(mm):
        return mm * 2.83465

    crop_height = mm_to_points(90)
    crop_width = mm_to_points(195)

    pdf_buffer.seek(0)
    reader = PyPDF2.PdfReader(pdf_buffer)
    writer = PyPDF2.PdfWriter()

    for page in reader.pages:
        current_left, current_bottom = map(float, page.mediabox.lower_left)
        current_right, current_top = map(float, page.mediabox.upper_right)

        current_width = current_right - current_left
        current_height = current_top - current_bottom

        additional_crop = mm_to_points(21)
        crop_left = max(0, (current_width - crop_width) / 2)
        crop_bottom = max(0, (current_height - crop_height) / 2)
        crop_right = max(0, (current_width - crop_width) / 2) + additional_crop
        crop_top = max(0, (current_height - crop_height) / 2)

        new_left = current_left + crop_left
        new_bottom = current_bottom + crop_bottom
        new_right = current_right - crop_right
        new_top = current_top - crop_top

        page.mediabox.lower_left = (new_left, new_bottom)
        page.mediabox.upper_right = (new_right, new_top)
        writer.add_page(page)

    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer


def send_webhook(pdf_buffer, name):
    pdf_buffer.seek(0)
    files = {'file': (name, pdf_buffer)}
    requests.post(discordWebhook, files=files)


def check_dpd(file_buffer):
    file_buffer.seek(0)
    pdf_text = PyPDF2.PdfReader(file_buffer).pages[0].extract_text()
    return "dpd" in pdf_text.lower()


def handle_dpd(file_buffer):
    file_buffer.seek(0)
    pdf = PyPDF2.PdfReader(file_buffer)
    writer = PyPDF2.PdfWriter()

    for page in pdf.pages:
        width = page.mediabox.width
        height = page.mediabox.height
        page.mediabox.lower_left = (0, height / 2)
        page.mediabox.upper_right = (width / 2, height)
        writer.add_page(page)

    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer, len(pdf.pages)


def main(paths):
    processed_buffers = []
    label_count = 0
    carrier = "c"

    # Sammle alle PDF-Dateien
    files = []
    if len(paths) > 1:
        print("Multiple files selected.")
        files = [path for path in paths if path.lower().endswith('.pdf')]
    elif os.path.isdir(paths[0]):
        dir_path = paths[0]
        files = [os.path.join(dir_path, f) for f in os.listdir(dir_path)
                 if f.lower().endswith('.pdf')]
    else:
        files = [paths[0]]

    # Verarbeite jede Datei
    for file_path in files:
        with open(file_path, 'rb') as f:
            file_buffer = io.BytesIO(f.read())

        if check_dpd(file_buffer):
            carrier += "_DPD"
            processed_buffer, count = handle_dpd(file_buffer)
            label_count += count
            processed_buffers.append(processed_buffer)
        elif check_retoure(file_buffer):
            processed_buffer = extract_and_rotate_images(file_buffer)
            carrier += "_Retoure"
            processed_buffers.append(processed_buffer)
        else:
            split_buffer = split_and_rotate(file_buffer)
            cropped_buffer = crop_pdf_to_format(split_buffer)
            carrier += "_DHL"
            processed_buffers.append(cropped_buffer)

    if processed_buffers:
        merged_buffer = concatenate_buffers(processed_buffers)

        if discordWebhook:
            send_webhook(merged_buffer, name=f"{carrier}_{label_count}_labels.pdf")

        if openFiles:
            temp_path = f"temp_merged_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
            with open(temp_path, 'wb') as temp_file:
                merged_buffer.seek(0)
                temp_file.write(merged_buffer.read())
            os.startfile(temp_path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print("No files selected. Please right-click on PDF files and select the script from the context menu.")