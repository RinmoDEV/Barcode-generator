from flask import Flask, request, render_template, send_file
import os
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF
import pytesseract
from PIL import Image
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
    
    try:
        # Process image to extract codes
        img = Image.open(image_path)
        
        # Preprocess image for better OCR
        img = img.convert('L')  # Convert to grayscale
        img = img.point(lambda x: 0 if x < 128 else 255)  # Increase contrast
        
        # Extract text using Tesseract
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        # Find codes matching pattern (adjust regex as needed)
        code_pattern = r'I\d{5}-\d{7}-\d{7}'
        extracted_codes = re.findall(code_pattern, text)
        
        if not extracted_codes:
            return render_template('index.html', error='No valid codes found in image')
            
    except Exception as e:
        return render_template('index.html', error=f'Error processing image: {str(e)}')
    
    # Generate PDF with barcodes
    pdf_path = generate_barcode_pdf(extracted_codes)
    
    return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')

@app.route('/generate', methods=['POST'])
def generate_from_text():
    codes_text = request.form.get('codes', '')
    if not codes_text.strip():
        return render_template('index.html', error='No codes provided')
    
    # Split the text into lines and remove empty lines
    codes = [line.strip() for line in codes_text.split('\n') if line.strip()]
    
    # Generate PDF with barcodes
    pdf_path = generate_barcode_pdf(codes)
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')

def generate_barcode_pdf(codes):
    temp_dir = app.config['TEMP_FOLDER']
    output_pdf = os.path.join(temp_dir, "barcodes.pdf")
    
    # Generate barcode images
    barcode_files = []
    for code in codes:
        ean = barcode.Code128(code, writer=ImageWriter())
        filename = os.path.join(temp_dir, f"{code}.png")
        ean.save(filename)
        barcode_files.append(filename)
    
    # A4 page size in mm
    A4_WIDTH, A4_HEIGHT = 210, 297
    BARCODE_WIDTH = 80
    BARCODE_HEIGHT = 25
    SPACING = 8
    MARGIN_X = (A4_WIDTH - BARCODE_WIDTH) / 2
    
    # Create a PDF object
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=5)
    
    # Add barcodes to PDF - all on one page
    pdf.add_page()
    
    # Calculate the total height of all barcodes + spacing
    total_group_height = (len(codes) * BARCODE_HEIGHT) + ((len(codes) - 1) * SPACING)
    start_y = (A4_HEIGHT - total_group_height) / 2
    
    # Add all barcodes to the single page
    for j in range(len(codes)):
        img_path = barcode_files[j]
        x_pos = MARGIN_X
        y_pos = start_y + j * (BARCODE_HEIGHT + SPACING)
        
        # Add the barcode image
        pdf.image(img_path, x=x_pos, y=y_pos, w=BARCODE_WIDTH, h=BARCODE_HEIGHT)
    
    # Save the PDF
    pdf.output(output_pdf)
    
    return output_pdf

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
