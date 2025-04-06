from flask import Flask, request, send_file, Response
import os
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF

app = Flask(__name__)
app.config['TEMP_FOLDER'] = 'temp'
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Barcode Generator</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #121212;
                color: #e0e0e0;
            }
            .container {
                max-width: 800px;
                margin: 40px auto;
                padding: 30px;
                background: #1e1e1e;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            h1 {
                color: #ffffff;
                text-align: center;
                margin-bottom: 30px;
            }
            textarea {
                width: 100%;
                height: 180px;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid #333;
                border-radius: 4px;
                font-family: monospace;
                font-size: 14px;
                resize: vertical;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            .btn {
                display: block;
                width: 100%;
                padding: 12px;
                background: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #b71c1c;
            }
            .instructions {
                margin-top: 20px;
                padding: 15px;
                background: #2d2d2d;
                border-left: 4px solid #d32f2f;
                font-size: 14px;
            }
            footer {
                text-align: center;
                margin-top: 30px;
                color: #777;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Barcode Generator</h1>
            <form method="POST" action="/generate">
                <textarea name="codes" placeholder="Enter codes here, one per line"></textarea>
                <button type="submit" class="btn">Generate Barcodes</button>
            </form>
            <div class="instructions">
                <p><strong>Instructions:</strong></p>
                <ul>
                    <li>Enter one code per line</li>
                    <li>Codes will be generated as Code128 barcodes</li>
                    <li>The PDF will contain 8 barcodes per page</li>
                </ul>
            </div>
            <footer>
                &copy; 2023 Barcode Generator
            </footer>
        </div>
    </body>
    </html>
    """

@app.route('/generate', methods=['POST'])
def generate_from_text():
    try:
        codes_text = request.form.get('codes', '')
        if not codes_text.strip():
            return index()
        
        codes = [line.strip() for line in codes_text.split('\n') if line.strip()]
        pdf_path = generate_barcode_pdf(codes)
        
        return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')
    except Exception as e:
        return Response(f"An error occurred: {str(e)}", status=500)

def generate_barcode_pdf(codes):
    temp_dir = app.config['TEMP_FOLDER']
    output_pdf = os.path.join(temp_dir, "barcodes.pdf")
    
    # Clean up old files
    for file in os.listdir(temp_dir):
        if file.endswith(".png"):
            try: os.remove(os.path.join(temp_dir, file))
            except: pass
    
    # Generate all barcode images first
    barcode_files = []
    for i, code in enumerate(codes):
        filename = os.path.join(temp_dir, f"barcode_{i}.png")
        try:
            ean = barcode.Code128(code, writer=ImageWriter())
            ean.save(filename.rsplit('.', 1)[0])
            actual_filename = filename if os.path.exists(filename) else filename.rsplit('.', 1)[0] + '.png'
            barcode_files.append(actual_filename)  # Store only filename, not code
        except Exception as e:
            print(f"Error generating barcode for code {code}: {str(e)}")
    
    # Create PDF with 8 barcodes per page (2x4 grid) with better spacing
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    for i, img_path in enumerate(barcode_files):
        if i > 0 and i % 8 == 0:
            pdf.add_page()
        
        col = (i % 8) % 2  # 2 columns (0-1)
        row = (i % 8) // 2  # 4 rows (0-3)
        x_pos = 25 + col * 90  # Adjusted spacing
        y_pos = 25 + row * 60  # More vertical space
        
        # Add barcode image only, no text
        pdf.image(img_path, x=x_pos, y=y_pos, w=80, h=25)
    
    pdf.output(output_pdf)
    return output_pdf

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
