import tkinter as tk
from tkinter import messagebox
from binders import (
    path_initialize,
    directory_reader,
    generate_report,
)
from rawdata import template_generator



#Initialize program inputs.
template, rawdata_folder, budget_folder, sequence = path_initialize()

#Interfacing.
root = tk.Tk()

canvas = tk.Canvas(root, width=600, height=300)
canvas.grid(columnspan=3, rowspan=3)

#Feedback textbox
text_box = tk.Text(root, height=30, width=70, padx=15, pady=15)
text_box.grid(column=1, columnspan=2, row=0, rowspan=3)

text_box.insert(1.0, '++ Inicializando...\n')

plantilla, display_str = directory_reader(template, rawdata_folder, budget_folder)

text_box.insert('end', display_str)


#Menu buttons
def read_instructions():
    application_path = template.parent
    instructions_path = application_path / 'static_files' / 'instructions.txt'

    if not instructions_path.exists():
        messagebox.showwarning(
            'Instrucciones',
            f'No se encontró el archivo de instrucciones:\n{instructions_path}',
        )
        return

    instructions = instructions_path.read_text(encoding='utf-8')
    messagebox.showinfo('Instrucciones', instructions)

def generate_report_interface():
    display_str = generate_report(rawdata_folder, budget_folder, sequence)
    text_box.insert('end', display_str)
    text_box.see('end')

def generate_template_interface():
    _, display_str = template_generator(template)
    print(display_str, end='')
    text_box.insert('end', display_str)
    text_box.see('end')
    
#Read Instructions
instruction_text = tk.StringVar()
instruction_btn = tk.Button(root, textvariable=instruction_text, command=read_instructions, fg="black")
instruction_text.set('Ver Instrucciones')
instruction_btn.grid(column=0, row=0)

#Download Example
example_text = tk.StringVar()
example_btn = tk.Button(
    root,
    textvariable=example_text,
    command=generate_template_interface,
    fg="black",
)
example_text.set('Descargar Plantilla de Ejemplo')
example_btn.grid(column=0,row=1)

#Generate Report
generate_text = tk.StringVar()
generate_btn = tk.Button(root, textvariable=generate_text, command=lambda:generate_report_interface(), fg="black")
generate_text.set('Generar Reporte')
generate_btn.grid(column=0,row=2)



root.mainloop()