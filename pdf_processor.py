import io
import os
import datetime
import glob
import shutil
import sys
import PyPDF2
import pdfrw
import requests
from readConfig import discordWebhook, openFiles
import fitz # PyMuPDF
from PIL import Image


def check_private(filename):
    file = PyPDF2.PdfReader(filename)
    numPages = len(file.pages)
    searchItems = ["Warenkorb-Nr", "Privat"]
    for i in range(0, numPages):
        page = file.pages[i]
        text = page.extract_text()
        if any(item in text for item in searchItems):
            return True
    return False

def check_Retoure(filename):
    file = PyPDF2.PdfReader(filename)
    numPages = len(file.pages)
    searchItems = ["Rücksendeetikett", "Rücksendezentrum", "Returns Centre"]
    for i in range(0, numPages):
        page = file.pages[i]
        text = page.extract_text()
        if any(item in text for item in searchItems):
            return True
    return False


def extract_and_rotate_images(filename, outPath):
    doc = fitz.open(filename)
    pdf_writer = PyPDF2.PdfWriter()

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            image = Image.open(io.BytesIO(doc.extract_image(img[0])["image"]))
            rotated_image = image.rotate(270, expand=True)
            img_byte_arr = io.BytesIO()
            rotated_image.save(img_byte_arr, format='PDF')
            img_byte_arr = img_byte_arr.getvalue()

            pdf_image = PyPDF2.PdfReader(io.BytesIO(img_byte_arr))
            pdf_writer.add_page(pdf_image.pages[0])

    output_pdf_path = os.path.join(outPath, os.path.basename(filename).split('.')[0] + "_edited.pdf")
    with open(output_pdf_path, "wb") as output_file:
        pdf_writer.write(output_file)

    doc.close()
    return output_pdf_path


def split_and_rotate(filename, outPath):
    writer = pdfrw.PdfWriter()
    filepath = os.path.join(outPath, os.path.basename(filename).split('.')[0] + "_edited.pdf")
    for page in pdfrw.PdfReader(filename).pages:
        newpage = pdfrw.PageMerge()
        newpage.add(page, viewrect=(0, 0, 1, 0.5))
        page = newpage.render()
        page.Rotate = 90
        writer.addpage(page)
    writer.write(filepath)
    return filepath

def concatenate(outpath):
    writer = pdfrw.PdfWriter()
    for file in glob.glob(os.path.join(outpath, "*.pdf")):
        reader = pdfrw.PdfReader(file)
        writer.addpages(reader.pages)
    merged_path = os.path.join(outpath, "merged.pdf")
    writer.write(merged_path)
    return merged_path


def crop_pdf_to_format(path, target_format):

    def mm_to_points(mm):
        return mm * 2.83465

    def inches_to_points(inches):
        return inches * 72

    crop_height = mm_to_points(105)  # 105 mm in points
    crop_width = mm_to_points(208) # 208 mm in points

    width, height = map(float, target_format.lower().replace("mm", "").split('x'))
    if 'mm' in target_format.lower():
        target_width = mm_to_points(width)
        target_height = mm_to_points(height)
    else:
        target_width = inches_to_points(width)
        target_height = inches_to_points(height)

    reader = PyPDF2.PdfReader(path)
    writer = PyPDF2.PdfWriter()

    for page in reader.pages:
        current_left, current_bottom = map(float, page.mediabox.lower_left)
        current_right, current_top = map(float, page.mediabox.upper_right)

        current_width = current_right - current_left
        current_height = current_top - current_bottom

        crop1_left = max(0, (current_width - crop_width) / 2)
        crop1_bottom = max(0, (current_height - crop_height) / 2)
        crop1_right = max(0, (current_width - crop_width) / 2)
        crop1_top = max(0, (current_height - crop_height) / 2)

        new_left1 = current_left + crop1_left
        new_bottom1 = current_bottom + crop1_bottom
        new_right1 = current_right - crop1_right
        new_top1 = current_top - crop1_top

        page.mediabox.lower_left = (new_left1, new_bottom1)
        page.mediabox.upper_right = (new_right1, new_top1)

        # page.scale_to(target_height, target_width)
        writer.add_page(page)

    with open(path, "wb") as output_file:
        writer.write(output_file)

    return path


def send_webhook(pathToMerged):
    with open(pathToMerged, "rb") as file:
        files = {'file': ('path', file)}
        requests.post(discordWebhook, files=files)


def main(paths):
    if not os.path.exists("./RetourenLabels"):
        os.mkdir("./RetourenLabels")
    if not os.path.exists("./EditedLabels"):
        os.mkdir("./EditedLabels")
    files = []

    outPath = "./EditedLabels/" + datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

    if len(paths) > 1:
        print("Multiple files selected.")
        for file_path in paths:
            if file_path.lower().endswith('.pdf'):
                shutil.copy(file_path, "./RetourenLabels")
                files.append(file_path)
            else:
                print(f"Skipping file: {file_path} (not a PDF file)")
    elif os.path.isdir(paths[0]):
        for file in os.listdir(paths[0]):
            if file.lower().endswith('.pdf'):
                shutil.copy(os.path.join(paths[0], file), "./RetourenLabels")
                files.append(os.path.join(paths[0], file))
            else:
                print(f"Skipping file: {file} (not a PDF file)")
    else:
        files.append(paths[0])

    if not os.path.exists(outPath) and len(files) > 0:
        os.mkdir(outPath)
    for file in files:
        if check_Retoure(file):
            extract_and_rotate_images(file, outPath)
        else:
            out_pdf_path = split_and_rotate(file, outPath)
            # if not check_private(file):
            crop_pdf_to_format(out_pdf_path, "105x208mm")
    merged_path = concatenate(outPath)

    if discordWebhook:
        send_webhook(merged_path)
    if openFiles:
        os.startfile(merged_path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print("No files selected. Please right-click on PDF files and select the script from the context menu.")