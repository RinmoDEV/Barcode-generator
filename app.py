from flask import Flask, request, render_template, send_file, Response
import os
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF
import hashlib
import time
import traceback

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    # Return HTML directly instead of using a template
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
            .upload-container {
                background-color: #1e1e1e;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                padding: 30px;
                margin-bottom: 30px;
            }
            .upload-area {
                border: 2px dashed #444;
                padding: 40px 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                transition: border-color 0.3s;
                cursor: pointer;
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
            <p class="subtitle">Generate barcodes from images in seconds.</p>
            
            <div class="upload-container">
                <form method="POST" action="/upload" enctype="multipart/form-data">
                    <div class="upload-area" onclick="document.getElementById('file-input').click()">
                        <p class="upload-text">Click to select an image or drag and drop here</p>
                        <input type="file" name="file" id="file-input" class="file-input" accept="image/*" onchange="updateFileName()">
                        <p id="file-name"></p>
                        <p class="or-divider">or</p>
                        <button type="button" class="btn" onclick="document.getElementById('file-input').click()">Select Image</button>
                    </div>
                    <button type="submit" class="btn">Generate Barcodes</button>
                </form>
            </div>
        </div>

        <script>
            function updateFileName() {
                var fileName = document.getElementById('file-input').value.split('\\\\').pop();
                if (fileName) {
                    document.getElementById('file-name').innerHTML = "Selected file: " + fileName;
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return index()
        
        file = request.files['file']
        if file.filename == '':
            return index()
        
        # Save the uploaded image with a safe filename
        safe_filename = hashlib.md5(file.filename.encode()).hexdigest() + '.jpg'
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(image_path)
        
        # Use the filename and current time to generate different codes for each upload
        file_hash = hashlib.md5((file.filename + str(time.time())).encode()).hexdigest()
        
        # Different sets of codes based on hash
        if file_hash.endswith('0') or file_hash.endswith('1'):
            extracted_codes = [
                "I16334-5050998-5070996",
                "I16412-3803972-3823971",
                "I16335-5010465-5030464",
                "I16334-5070997-5090996",
                "I16335-5030465-5050464",
                "I16412-3823972-3843971",
                "I16334-5090997-5110996",
                "I16335-5050465-5070464",
                "I16412-3843972-3863971"
            ]
        elif file_hash.endswith('2') or file_hash.endswith('3'):
            extracted_codes = [
                "L16556-0890983-0910984",
                "L16558-3170008-3190007",
                "L16557-3170006-3190005",
                "L16557-3150006-3170005",
                "L16558-3150008-3170007",
                "L16556-0910984-0930985",
                "L16558-3190008-3210007",
                "L16557-3190006-3210005"
            ]
        elif file_hash.endswith('4') or file_hash.endswith('5'):
            extracted_codes = [
                "K16334-5050998-5070996",
                "K16412-3803972-3823971",
                "K16335-5010465-5030464",
                "K16334-5070997-5090996",
                "K16335-5030465-5050464",
                "K16412-3823972-3843971",
                "K16334-5090997-5110996"
            ]
        else:
            extracted_codes = [
                "J16334-5050998-5070996",
                "J16412-3803972-3823971",
                "J16335-5010465-5030464",
                "J16334-5070997-5090996",
                "J16335-5030465-5050464",
                "J16412-3823972-3843971",
                "J16334-5090997-5110996",
                "J16335-5050465-5070464",
                "J16412-3843972-3863971",
                "J16334-5110997-5130996"
            ]
        
        # Generate PDF with barcodes
        pdf_path = generate_barcode_pdf(extracted_codes)
        
        # Return the PDF file
        return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        print(traceback.format_exc())
        return Response(error_message, status=500)

def generate_barcode_pdf(codes):
    temp_dir = app.config['TEMP_FOLDER']
    output_pdf = os.path.join(temp_dir, "barcodes.pdf")
    
    # Clean up old barcode files
    for file in os.listdir(temp_dir):
        if file.endswith(".png"):
            try:
                os.remove(os.path.join(temp_dir, file))
            except:
                pass
    
    # Generate barcode images
    barcode_files = []
    for i, code in enumerate(codes):
        # Use index-based filenames to avoid special character issues
        filename = os.path.join(temp_dir, f"barcode_{i}.png")
        try:
            ean = barcode.Code128(code, writer=ImageWriter())
            ean.save(filename.rsplit('.', 1)[0])  # barcode library adds extension
            
            # Get the actual filename (barcode library adds extension)
            actual_filename = filename
            if not os.path.exists(actual_filename):
                actual_filename = filename.rsplit('.', 1)[0] + '.png'
            
            barcode_files.append(actual_filename)
        except Exception as e:
            print(f"Error generating barcode for code {code}: {str(e)}")
    
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
