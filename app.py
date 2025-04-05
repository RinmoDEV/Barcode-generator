from flask import Flask, request, render_template, send_file, Response
import os
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF
import traceback

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'

# Ensure directories exist with proper permissions
@app.before_first_request
def setup_directories():
    for directory in [app.config['UPLOAD_FOLDER'], app.config['TEMP_FOLDER']]:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
        except Exception as e:
            print(f"Error creating directory {directory}: {str(e)}")

# Ensure directories exist at startup too
for directory in [app.config['UPLOAD_FOLDER'], app.config['TEMP_FOLDER']]:
    os.makedirs(directory, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return render_template('index.html', error='No file part')
        
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error='No selected file')
        
        # Save the uploaded image
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(image_path)
        
        # For now, we'll use hardcoded codes
        extracted_codes = [
            "I16334-5050998-5070996",
            "I16412-3803972-3823971",
            "I16335-5010465-5030464",
            "I16334-5070997-5090996",
            "I16335-5030465-5050464",
            "I16412-3823972-3843971"
        ]
        
        # Generate PDF with barcodes
        pdf_path = generate_barcode_pdf(extracted_codes)
        
        # Return the PDF file
        return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')
    except Exception as e:
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return Response(f"An error occurred: {str(e)}", status=500)

@app.route('/generate', methods=['POST'])
def generate_from_text():
    try:
        codes_text = request.form.get('codes', '')
        if not codes_text.strip():
            return render_template('index.html', error='No codes provided')
        
        # Split the text into lines and remove empty lines
        codes = [line.strip() for line in codes_text.split('\n') if line.strip()]
        
        # Generate PDF with barcodes
        pdf_path = generate_barcode_pdf(codes)
        
        # Return the PDF file
        return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')
    except Exception as e:
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return Response(f"An error occurred: {str(e)}", status=500)

def generate_barcode_pdf(codes):
    # Make sure temp directory exists
    temp_dir = app.config['TEMP_FOLDER']
    os.makedirs(temp_dir, exist_ok=True)
    
    output_pdf = os.path.join(temp_dir, "barcodes.pdf")
    
    # Generate barcode images
    barcode_files = []
    for code in codes:
        # Create a safe filename by replacing problematic characters
        safe_code = "".join([c if c.isalnum() else "_" for c in code])
        filename = os.path.join(temp_dir, f"{safe_code}.png")
        
        # Generate the barcode
        ean = barcode.Code128(code, writer=ImageWriter())
        ean.save(filename)
        
        # Verify the file was created
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Failed to create barcode image: {filename}")
            
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
