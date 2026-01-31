import sys
import os
import re
from fpdf import FPDF

class ProjectBookPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Ultra-Safe Layout: 40mm side margins (130mm usable width)
    pdf = ProjectBookPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(40, 30, 40) 
    pdf.set_auto_page_break(auto=True, margin=30)
    pdf.add_page()
    
    w = 130 

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Sanitization
    content = content.replace('**', '')
    content = re.sub(r'[^\x00-\x7F]+', ' ', content) # ASCII only for helvetica
    
    # Process by logical blocks (separated by double-newlines)
    blocks = content.split('\n\n')

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')
        first = lines[0].strip()

        # Handle Header 1
        if first.startswith('# '):
            pdf.ln(5)
            pdf.set_font("helvetica", 'B', 20)
            pdf.set_text_color(20, 40, 80)
            pdf.multi_cell(w, 12, first[2:].upper(), align='L')
            pdf.ln(2)
            remaining_text = " ".join(l.strip() for l in lines[1:])
            if remaining_text:
                pdf.set_font("helvetica", size=11)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(w, 6, remaining_text, align='L')
                pdf.ln(2)
        # Handle Header 2
        elif first.startswith('## '):
            pdf.ln(4)
            pdf.set_font("helvetica", 'B', 16)
            pdf.set_text_color(40, 70, 120)
            pdf.multi_cell(w, 10, first[3:], align='L')
            pdf.ln(2)
            remaining_text = " ".join(l.strip() for l in lines[1:])
            if remaining_text:
                pdf.set_font("helvetica", size=11)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(w, 6, remaining_text, align='L')
                pdf.ln(2)
        # Handle Header 3
        elif first.startswith('### '):
            pdf.ln(3)
            pdf.set_font("helvetica", 'B', 14)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(w, 8, first[4:], align='L')
            pdf.ln(2)
            remaining_text = " ".join(l.strip() for l in lines[1:])
            if remaining_text:
                pdf.set_font("helvetica", size=11)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(w, 6, remaining_text, align='L')
                pdf.ln(2)
        # Handle Header 4
        elif first.startswith('#### '):
            pdf.ln(2)
            pdf.set_font("helvetica", 'B', 12)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(w, 7, first[5:], align='L')
            pdf.ln(2)
            remaining_text = " ".join(l.strip() for l in lines[1:])
            if remaining_text:
                pdf.set_font("helvetica", size=11)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(w, 6, remaining_text, align='L')
                pdf.ln(2)
        # Handle Images
        elif first.startswith('!['):
            img_path = first.split('(')[1].split(')')[0]
            if os.path.exists(img_path):
                pdf.ln(5)
                pdf.image(img_path, w=w)
                pdf.ln(5)
        # Handle Lists
        elif first.startswith('- '):
            pdf.set_font("helvetica", size=11)
            pdf.set_text_color(0, 0, 0)
            for list_line in lines:
                list_line = list_line.strip()
                if list_line.startswith('- '):
                    pdf.multi_cell(w, 7, f" - {list_line[2:]}", align='L')
            pdf.ln(2)
        # Handle Horizontal Rules
        elif first.startswith('---'):
            pdf.ln(2)
            pdf.line(40, pdf.get_y(), 170, pdf.get_y())
            pdf.ln(4)
        # Handle Numbered Lists
        elif re.match(r'^\d+\. ', first):
            pdf.set_font("helvetica", size=11)
            pdf.set_text_color(0, 0, 0)
            for list_line in lines:
                list_line = list_line.strip()
                if re.match(r'^\d+\. ', list_line):
                    pdf.multi_cell(w, 7, list_line, align='L')
            pdf.ln(2)
        # Handle Regular Paragraphs
        else:
            pdf.set_font("helvetica", size=11)
            pdf.set_text_color(0, 0, 0)
            clean_text = " ".join(l.strip() for l in lines)
            pdf.multi_cell(w, 6, clean_text, align='L')
            pdf.ln(4)

    pdf.output(output_file)
    print(f"Professional PDF generated: {output_file} ({pdf.page_no()} pages)")

if __name__ == "__main__":
    generate_pdf("project_book_content.md", "Torrpeddo_Project_Book.pdf")
