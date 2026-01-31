import sys
import os
from fpdf import FPDF

class ProjectBookPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Torrpeddo Project Book', border=False, align='C')
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
    pdf.set_font("helvetica", size=12)
    
    # Use a safe usable width
    effective_width = pdf.w - 40 # 20mm margins on both sides

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by double newlines for paragraphs to make it easier
    blocks = content.split('\n')

    for line in blocks:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
        
        if line.startswith('# '):
            pdf.set_font("helvetica", 'B', 24)
            pdf.multi_cell(effective_width, 15, line[2:])
            pdf.ln(5)
        elif line.startswith('## '):
            pdf.set_font("helvetica", 'B', 18)
            pdf.ln(5)
            pdf.multi_cell(effective_width, 12, line[3:])
            pdf.ln(2)
        elif line.startswith('### '):
            pdf.set_font("helvetica", 'B', 14)
            pdf.ln(2)
            pdf.multi_cell(effective_width, 10, line[4:])
        elif line.startswith('- '):
            pdf.set_font("helvetica", size=12)
            pdf.multi_cell(effective_width, 8, f"  - {line[2:]}")
        elif line.startswith('---'):
            pdf.ln(2)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(5)
        else:
            pdf.set_font("helvetica", size=12)
            pdf.multi_cell(effective_width, 7, line)

    pdf.output(output_file)
    print(f"PDF generated successfully: {output_file}")

if __name__ == "__main__":
    input_md = "project_book_content.md"
    output_pdf = "Torrpeddo_Project_Book.pdf"
    generate_pdf(input_md, output_pdf)
