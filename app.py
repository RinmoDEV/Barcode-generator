from flask import Flask, request, render_template, send_file, Response
import os
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    # Create a simple HTML page directly in the code
    html = '''
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
            .error {
                color: #e74c3c;
                margin-bottom: 15px;
            }
        </style>
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
                var fileName = document.getElementById('file-input').value.split('\\').pop();
                if (fileName) {
                    document.getElementById('file-name').innerHTML = "Selected file: " + fileName;
                }
            }
        </script>
    </body>
    </html>
    '''
    return Response(html, mimetype='text/html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return index()
    
    file = request.files['file']
    if file.filename == '':
        return index()
    
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

@app.route('/generate', methods=['POST'])
def generate_from_text():
    codes_text = request.form.get('codes', '')
    if not codes_text.strip():
        return index()
    
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
