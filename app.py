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
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Barcode Generator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            textarea { width: 100%; height: 150px; margin-bottom: 20px; }
            .btn { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Barcode Generator</h1>
        <form method="POST" action="/generate">
            <textarea name="codes" placeholder="Enter codes here, one per line"></textarea>
            <button type="submit" class="btn">Generate Barcodes</button>
        </form>
    </body>
    </html>
    '''

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
        filename = os.path.join(temp_dir, f"barcode_{i}.png")
        try:
            ean = barcode.Code128(code, writer=ImageWriter())
            ean.save(filename.rsplit('.', 1)[0])
            actual_filename = filename if os.path.exists(filename) else filename.rsplit('.', 1)[0] + '.png'
            barcode_files.append(actual_filename)
        except Exception as e:
            print(f"Error generating barcode for code {code}: {str(e)}")
    
    # Create PDF
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=5)
    pdf.add_page()
    
    # Add barcodes to PDF
    for j, img_path in enumerate(barcode_files):
        x_pos = 15
        y_pos = 10 + j * 30
        pdf.image(img_path, x=x_pos, y=y_pos, w=80, h=25)
    
    pdf.output(output_pdf)
    return output_pdf

if __name__ == '__main__':
    app.run(debug=True)
