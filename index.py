import tkinter as tk
from tkinter import *
from tkinter import ttk

root = Tk()

root.title('Metin Bot')
root.geometry("500x500")
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Settings").grid(column=0, row=0)
ttk.Label(frm, text="Auto Pickup").grid(column=0, row=1)
ttk.Label(frm, text="Offset X").grid(column=0, row=2)
ttk.Label(frm, text="Offset Y").grid(column=0, row=3)

ttk.Checkbutton(frm).grid(column=1, row=1)

offset_x_text_var = tk.StringVar()
offset_x_text_var.set('75')
ttk.Entry(frm, textvariable=offset_x_text_var).grid(column=1, row=2)

offset_y_text_var = tk.StringVar()
offset_y_text_var.set('85')
ttk.Entry(frm, textvariable=offset_y_text_var).grid(column=1, row=3)

ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)

root.mainloop()
