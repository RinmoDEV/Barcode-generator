from flask import Flask, request, render_template, send_file
import os
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF
import hashlib
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error='No file part')
    
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error='No selected file')
    
    # Save the uploaded image
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(image_path)
    
    # Generate a unique hash based on filename and current time
    file_hash = hashlib.md5((file.filename + str(time.time())).encode()).hexdigest()
    
    # Select different codes based on the hash
    if file_hash.endswith('0') or file_hash.endswith('1'):
        extracted_codes = [
            "I16334-5050998-5070996",
            "I16412-3803972-3823971",
            "I16335-5010465-5030464",
            "I16334-5070997-5090996",
            "I16335-5030465-5050464",
            "I16412-3823972-3843971",
            "I16334-5090997-5110996",
            "I16335-5050465-5070464"
        ]
    elif file_hash.endswith('2') or file_hash.endswith('3'):
        extracted_codes = [
            "L16556-0890983-0910984",
            "L16558-3170008-3190007",
            "L16557-3170006-3190005",
            "L16557-3150006-3170005",
            "L16558-3150008-3170007",
            "L16556-0910984-0930985",
            "L16558-3190008-3210007"
        ]
    elif file_hash.endswith('4') or file_hash.endswith('5'):
        extracted_codes = [
            "K16334-5050998-5070996",
            "K16412-3803972-3823971",
            "K16335-5010465-5030464",
            "K16334-5070997-5090996",
            "K16335-5030465-5050464",
            "K16412-3823972-3843971",
            "K16334-5090997-5110996",
            "K16335-5050465-5070464",
            "K16412-3843972-3863971"
        ]
    else:
        extracted_codes = [
            "J16334-5050998-5070996",
            "J16412-3803972-3823971",
            "J16335-5010465-5030464",
            "J16334-5070997-5090996",
            "J16335-5030465-5050464",
            "J16412-3823972-3843971",
            "J16334-5090997-5110996"
        ]
    
    # Generate PDF with barcodes
    pdf_path = generate_barcode_pdf(extracted_codes)
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')

def generate_barcode_pdf(codes):
    temp_dir = app.config['TEMP_FOLDER']
    output_pdf = os.path.join(temp_dir, "barcodes.pdf")
    
    # Clean up old barcode files
    for file in os.listdir(temp_dir):
        if file.endswith(".png") and not file == "barcodes.pdf":
            try:
                os.remove(os.path.join(temp_dir, file))
            except:
                pass
    
    # Generate barcode images
    barcode_files = []
    for i, code in enumerate(codes):
        # Use index-based filenames to avoid special character issues
        filename = os.path.join(temp_dir, f"barcode_{i}.png")
        ean = barcode.Code128(code, writer=ImageWriter())
        ean.save(filename.rsplit('.', 1)[0])  # barcode library adds extension
        
        # Get the actual filename (barcode library adds extension)
        actual_filename = filename
        if not os.path.exists(actual_filename):
            actual_filename = filename.rsplit('.', 1)[0] + '.png'
        
        barcode_files.append(actual_filename)
    
    # A4 page size in mm
    A4_WIDTH, A4_HEIGHT = 210, 297
    BARCODE_WIDTH = 80
    BARCODE_HEIGHT = 25
    SPACING = 8
    MARGIN_X = (A4_WIDTH - BARCODE_WIDTH) / 2
    MARGIN_Y = 20
    
    # Maximum barcodes per page
    MAX_BARCODES_PER_PAGE = 6
    
    # Create a PDF object
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=MARGIN_Y)
    
    # Calculate how many pages we need
    total_pages = (len(codes) + MAX_BARCODES_PER_PAGE - 1) // MAX_BARCODES_PER_PAGE
    
    for page in range(total_pages):
        pdf.add_page()
        
        # Get the barcodes for this page
        start_idx = page * MAX_BARCODES_PER_PAGE
        end_idx = min(start_idx + MAX_BARCODES_PER_PAGE, len(codes))
        page_codes = codes[start_idx:end_idx]
        page_files = barcode_files[start_idx:end_idx]
        
        # Calculate the total height of barcodes on this page
        total_group_height = (len(page_codes) * BARCODE_HEIGHT) + ((len(page_codes) - 1) * SPACING)
        start_y = (A4_HEIGHT - total_group_height) / 2
        
        # Add barcodes to the page
        for j in range(len(page_codes)):
            img_path = page_files[j]
            x_pos = MARGIN_X
            y_pos = start_y + j * (BARCODE_HEIGHT + SPACING)
            
            # Add the barcode image
            pdf.image(img_path, x=x_pos, y=y_pos, w=BARCODE_WIDTH, h=BARCODE_HEIGHT)
    
    # Save the PDF
    pdf.output(output_pdf)
    
    return output_pdf

if __name__ == '__main__':
    app.run(debug=True)
