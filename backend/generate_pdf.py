import sys
import os
from fpdf import FPDF

class ProjectBookPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('helvetica', 'I', 8)
            self.cell(0, 10, 'Torrpeddo Project Book - Technical Documentation', border=False, align='R')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def generate_pdf(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    pdf = ProjectBookPDF()
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    
    effective_width = pdf.w - 40

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        
        # Handle Image Embedding
        if line.startswith('![Architecture Diagram]'):
            img_path = line.split('(')[1].split(')')[0]
            if os.path.exists(img_path):
                pdf.ln(5)
                # Center the image
                pdf.image(img_path, x=25, w=effective_width-10)
                pdf.ln(10)
            continue

        if not line:
            pdf.ln(5)
            continue
        
        if line.startswith('# '):
            pdf.set_font("helvetica", 'B', 28)
            pdf.set_text_color(20, 40, 80) # Dark blue
            pdf.multi_cell(effective_width, 20, line[2:].upper(), align='C')
            pdf.ln(10)
            pdf.set_text_color(0, 0, 0)
        elif line.startswith('## '):
            pdf.set_font("helvetica", 'B', 18)
            pdf.set_text_color(40, 70, 120)
            pdf.ln(5)
            pdf.multi_cell(effective_width, 12, line[3:])
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)
        elif line.startswith('### '):
            pdf.set_font("helvetica", 'B', 14)
            pdf.ln(2)
            pdf.multi_cell(effective_width, 10, line[4:])
        elif line.startswith('- '):
            pdf.set_font("helvetica", size=12)
            pdf.multi_cell(effective_width, 8, f"  - {line[2:]}")
        elif line.startswith('**'):
            # Simple bold detection (naive but works for this content)
            text = line.replace('**', '')
            pdf.set_font("helvetica", 'B', 12)
            pdf.multi_cell(effective_width, 7, text)
            pdf.set_font("helvetica", size=12)
        elif line.startswith('---'):
            pdf.ln(5)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(5)
        else:
            pdf.set_font("helvetica", size=12)
            pdf.multi_cell(effective_width, 7, line)

    pdf.output(output_file)
    print(f"Enhanced PDF generated successfully: {output_file}")

if __name__ == "__main__":
    input_md = "project_book_content.md"
    output_pdf = "Torrpeddo_Project_Book.pdf"
    generate_pdf(input_md, output_pdf)
