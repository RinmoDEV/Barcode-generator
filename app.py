from flask import Flask, request, render_template, send_file, Response
import os
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF
import traceback

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

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
        error_msg = f"Error in generate_from_text: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return Response(f"An error occurred: {str(e)}", status=500)

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
            "I16412-3823972-3843971",
            # Add more codes to test multiple pages
            "L16556-0890983-0910984",
            "L16558-3170008-3190007",
            "L16557-3170006-3190005",
            "L16557-3150006-3170005",
            "L16558-3150008-3170007",
            "L16556-0910984-0930985"
        ]
        
        # Generate PDF with barcodes
        pdf_path = generate_barcode_pdf(extracted_codes)
        
        # Return the PDF file
        return send_file(pdf_path, as_attachment=True, download_name='barcodes.pdf')
    except Exception as e:
        error_msg = f"Error in upload_file: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return Response(f"An error occurred: {str(e)}", status=500)

def generate_barcode_pdf(codes):
    try:
        temp_dir = app.config['TEMP_FOLDER']
        output_pdf = os.path.join(temp_dir, "barcodes.pdf")
        
        # Generate barcode images
        barcode_files = []
        for i, code in enumerate(codes):
            # Use a simple numeric filename to avoid special character issues
            filename = os.path.join(temp_dir, f"barcode_{i}.png")
            
            try:
                # Generate the barcode
                ean = barcode.Code128(code, writer=ImageWriter())
                ean.save(filename.rsplit('.', 1)[0])  # barcode library adds extension
                
                # Get the actual filename (barcode library adds extension)
                actual_filename = filename
                if not os.path.exists(actual_filename):
                    actual_filename = filename.rsplit('.', 1)[0] + '.png'
                
                # Verify the file was created
                if os.path.exists(actual_filename):
                    barcode_files.append((actual_filename, code))
                else:
                    print(f"Warning: File not created: {actual_filename}")
            except Exception as e:
                print(f"Error generating barcode for code {code}: {str(e)}")
        
        if not barcode_files:
            raise ValueError("No valid barcodes could be generated")
        
        # A4 page size in mm
        A4_WIDTH, A4_HEIGHT = 210, 297
        BARCODE_WIDTH = 80
        BARCODE_HEIGHT = 25
        SPACING = 10
        MARGIN_X = (A4_WIDTH - BARCODE_WIDTH) / 2
        MARGIN_Y = 20
        
        # Maximum barcodes per page (adjust as needed)
        MAX_BARCODES_PER_PAGE = 8
        
        # Create a PDF object
        pdf = FPDF(unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=MARGIN_Y)
        
        # Calculate how many pages we need
        total_pages = (len(barcode_files) + MAX_BARCODES_PER_PAGE - 1) // MAX_BARCODES_PER_PAGE
        
        for page in range(total_pages):
            pdf.add_page()
            
            # Get the barcodes for this page
            start_idx = page * MAX_BARCODES_PER_PAGE
            end_idx = min(start_idx + MAX_BARCODES_PER_PAGE, len(barcode_files))
            page_barcodes = barcode_files[start_idx:end_idx]
            
            # Calculate the total height of barcodes on this page
            total_group_height = (len(page_barcodes) * BARCODE_HEIGHT) + ((len(page_barcodes) - 1) * SPACING)
            start_y = (A4_HEIGHT - total_group_height) / 2
            
            # Add barcodes to the page
            for j, (img_path, code) in enumerate(page_barcodes):
                x_pos = MARGIN_X
                y_pos = start_y + j * (BARCODE_HEIGHT + SPACING)
                
                # Add the barcode image
                pdf.image(img_path, x=x_pos, y=y_pos, w=BARCODE_WIDTH, h=BARCODE_HEIGHT)
                
                # Add the code text below the barcode
                pdf.set_font('Arial', '', 10)
                pdf.set_xy(x_pos, y_pos + BARCODE_HEIGHT)
                pdf.cell(BARCODE_WIDTH, 5, code, 0, 1, 'C')
        
        # Save the PDF
        pdf.output(output_pdf)
        
        return output_pdf
    except Exception as e:
        error_msg = f"Error in generate_barcode_pdf: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
