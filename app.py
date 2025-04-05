from flask import Flask, request, send_file
import os
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF
import pytesseract
from PIL import Image
import re

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Create Flask app
app = Flask(__name__)

# Use absolute paths
app.config['UPLOAD_FOLDER'] = os.path.abspath('uploads')
app.config['TEMP_FOLDER'] = os.path.abspath('temp')

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Barcode Generator</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                box-sizing: border-box;
                font-family: Arial, sans-serif;
            }
            body {
                margin: 0;
                padding: 0;
                background-color: #121212;
                color: #e0e0e0;
            }
            header {
                background-color: #1e1e1e;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                padding: 10px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .logo {
                font-size: 24px;
                font-weight: bold;
                color: #e0e0e0;
            }
            .logo span {
                color: #e74c3c;
            }
            .main-container {
                max-width: 800px;
                margin: 40px auto;
                text-align: center;
            }
            h1 {
                font-size: 32px;
                color: #e0e0e0;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #aaaaaa;
                margin-bottom: 30px;
            }
            .tab-container {
                background-color: #1e1e1e;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                overflow: hidden;
                margin-bottom: 30px;
            }
            .tabs {
                display: flex;
                border-bottom: 1px solid #333;
            }
            .tab {
                padding: 15px 20px;
                cursor: pointer;
                flex: 1;
                text-align: center;
                transition: background-color 0.3s;
            }
            .tab.active {
                background-color: #2d2d2d;
                border-bottom: 3px solid #e74c3c;
                font-weight: bold;
            }
            .tab-content {
                display: none;
                padding: 30px;
            }
            .tab-content.active {
                display: block;
            }
            .upload-area {
                border: 2px dashed #444;
                padding: 40px 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                transition: border-color 0.3s;
            }
            .upload-area:hover {
                border-color: #e74c3c;
            }
            .btn {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            .btn:hover {
                background-color: #c0392b;
            }
            textarea {
                width: 100%;
                height: 150px;
                padding: 12px;
                border: 1px solid #444;
                border-radius: 5px;
                margin-bottom: 20px;
                resize: vertical;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            .file-input {
                display: none;
            }
            .upload-text {
                margin-bottom: 15px;
            }
            .or-divider {
                margin: 15px 0;
                color: #777;
            }
        </style>
        <script>
            function openTab(evt, tabName) {
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].className = tabcontent[i].className.replace(" active", "");
                }
                tablinks = document.getElementsByClassName("tab");
                for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }
                document.getElementById(tabName).className += " active";
                evt.currentTarget.className += " active";
            }
            
            function triggerFileInput() {
                document.getElementById('file-input').click();
            }
            
            function updateFileName() {
                var fileName = document.getElementById('file-input').value.split('\\\\').pop();
                if (fileName) {
                    document.getElementById('file-name').innerHTML = "Selected file: " + fileName;
                }
            }
        </script>
    </head>
    <body>
        <header>
            <div class="logo"><span>❤</span> CODETOPDF</div>
        </header>
        
        <div class="main-container">
            <h1>Barcode Generator</h1>
            <p class="subtitle">Generate barcodes from text or images in seconds.</p>
            
            <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="openTab(event, 'upload-tab')">Upload Image</div>
                    <div class="tab" onclick="openTab(event, 'text-tab')">Enter Codes</div>
                </div>
                
                <div id="upload-tab" class="tab-content active">
                    <form method="POST" action="/upload" enctype="multipart/form-data">
                        <div class="upload-area" onclick="triggerFileInput()">
                            <p class="upload-text">Click to select an image or drag and drop here</p>
                            <input type="file" name="file" id="file-input" class="file-input" accept="image/*" onchange="updateFileName()">
                            <p id="file-name"></p>
                            <p class="or-divider">or</p>
                            <button type="button" class="btn" onclick="triggerFileInput()">Select Image</button>
                        </div>
                        <button type="submit" class="btn">Generate Barcodes</button>
                    </form>
                </div>
                
                <div id="text-tab" class="tab-content">
                    <form method="POST" action="/generate">
                        <textarea name="codes" placeholder="Enter codes here, one per line&#10;Example:&#10;I16334-5050998-5070996&#10;I16412-3803972-3823971"></textarea>
                        <button type="submit" class="btn">Generate Barcodes</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

def extract_codes_from_image(image_path):
    """Extract codes from an image using OCR"""
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Extract text from the image
        text = pytesseract.image_to_string(img)
        print(f"Extracted text: {text}")
        
        # Replace $ with S and fix common OCR mistakes
        text = text.replace("$", "S")
        
        # Define patterns for different code formats
        patterns = [
            r'[ASL][0-9]{5}-[0-9]{7}-[0-9]{7}',  # A, S, L format
            r'I[0-9]{5}-[0-9]{7}-[0-9]{7}',      # I format
            r'1[0-9]{5}-[0-9]{7}-[0-9]{7}'       # 1 format (OCR might mistake I for 1)
        ]
        
        # Process the text line by line to catch all codes
        all_codes = []
        for line in text.split('\n'):
            for pattern in patterns:
                line_codes = re.findall(pattern, line)
                for code in line_codes:
                    # Fix codes that start with 1 but should start with I
                    if code[0] == '1' and re.match(r'1[0-9]{5}-[0-9]{7}-[0-9]{7}', code):
                        code = 'I' + code[1:]
                    
                    if code not in all_codes:
                        all_codes.append(code)
        
        print(f"Found {len(all_codes)} codes using multi-pattern approach")
        
        # If no codes found, try more aggressive OCR settings
        if not all_codes:
            print("No codes found with standard OCR, trying with custom configuration")
            # Try with different OCR configurations
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ASLI0123456789-'
            text = pytesseract.image_to_string(img, config=custom_config)
            print(f"Extracted text with custom config: {text}")
            
            # Try to find codes again
            for line in text.split('\n'):
                for pattern in patterns:
                    line_codes = re.findall(pattern, line)
                    for code in line_codes:
                        # Fix codes that start with 1 but should start with I
                        if code[0] == '1' and re.match(r'1[0-9]{5}-[0-9]{7}-[0-9]{7}', code):
                            code = 'I' + code[1:]
                        
                        if code not in all_codes:
                            all_codes.append(code)
            
            print(f"Found {len(all_codes)} codes after custom OCR configuration")
        
        # If still no codes found, return empty list
        if not all_codes:
            print("No codes found in the image")
            return []
        
        return all_codes
    except Exception as e:
        print(f"Error extracting codes: {e}")
        return []

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Error: No file part"
    
    file = request.files['file']
    if file.filename == '':
        return "Error: No selected file"
    
    # Save the uploaded image
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(image_path)
    
    # Extract codes from the uploaded image
    extracted_codes = extract_codes_from_image(image_path)
    
    # Check if any codes were found
    if not extracted_codes:
        return "Error: No valid codes found in the image. Please upload a clearer image with valid codes."
    
    # Generate PDF with barcodes
    pdf_path = generate_barcode_pdf(extracted_codes)
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')

@app.route('/generate', methods=['POST'])
def generate_from_text():
    codes_text = request.form.get('codes', '')
    if not codes_text.strip():
        return "Error: No codes provided"
    
    # Split the text into lines and remove empty lines
    codes = [line.strip() for line in codes_text.split('\n') if line.strip()]
    
    # Generate PDF with barcodes
    pdf_path = generate_barcode_pdf(codes)
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')

# Custom barcode writer class to disable text
class NoTextImageWriter(ImageWriter):
    def __init__(self):
        super().__init__()
        # Properly disable text in the barcode
        self.text = False
        self.font_size = 0
        self.quiet_zone = 1.0

def generate_barcode_pdf(codes):
    temp_dir = app.config['TEMP_FOLDER']
    output_pdf = os.path.join(temp_dir, "barcodes.pdf")
    
    # Clean temp directory first to avoid issues
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    
    # Generate barcode images
    barcode_files = []
    for code in codes:
        # Use our custom writer that disables text
        code_writer = barcode.Code128(code, writer=NoTextImageWriter())
        
        # Save with full path and get the actual filename that was saved
        saved_path = code_writer.save(os.path.join(temp_dir, code))
        print(f"Saved barcode image at: {saved_path}")
        barcode_files.append(saved_path)
    
    # A4 page size in mm
    A4_WIDTH, A4_HEIGHT = 210, 297
    BARCODE_WIDTH = 80
    BARCODE_HEIGHT = 25
    SPACING = 15
    MARGIN_X = (A4_WIDTH - BARCODE_WIDTH) / 2
    MARGIN_Y = 20
    
    # Create a PDF object
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=MARGIN_Y)
    
    # Calculate how many barcodes per page (5 per page)
    BARCODES_PER_PAGE = 5
    
    # Calculate total pages needed - ensure ALL codes are included
    total_pages = (len(codes) + BARCODES_PER_PAGE - 1) // BARCODES_PER_PAGE
    print(f"Total codes: {len(codes)}, creating {total_pages} pages")
    
    # Process ALL codes
    for page in range(total_pages):
        pdf.add_page()
        
        # Get codes for this page
        start_idx = page * BARCODES_PER_PAGE
        end_idx = min(start_idx + BARCODES_PER_PAGE, len(codes))
        page_codes = codes[start_idx:end_idx]
        page_files = barcode_files[start_idx:end_idx]
        
        print(f"Page {page+1}: Adding {len(page_codes)} barcodes (codes {start_idx+1} to {end_idx})")
        
        # Calculate spacing for this page
        available_height = A4_HEIGHT - (2 * MARGIN_Y)
        if len(page_codes) > 1:
            effective_spacing = (available_height - (len(page_codes) * BARCODE_HEIGHT)) / (len(page_codes) - 1)
            effective_spacing = min(effective_spacing, 30)  # Cap spacing to avoid too much space
        else:
            effective_spacing = 0
            
        # Add barcodes to this page
        for i, img_path in enumerate(page_files):
            # Verify file exists
            if not os.path.exists(img_path):
                print(f"Warning: Image file not found: {img_path}")
                continue
                
            x_pos = MARGIN_X
            y_pos = MARGIN_Y + i * (BARCODE_HEIGHT + effective_spacing)
            
            # Add the barcode image
            pdf.image(img_path, x=x_pos, y=y_pos, w=BARCODE_WIDTH, h=BARCODE_HEIGHT)
    
    # Save the PDF
    pdf.output(output_pdf)
    
    return output_pdf

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Temp folder: {app.config['TEMP_FOLDER']}")
    app.run(host='0.0.0.0', debug=True)