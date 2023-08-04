import os

import tkinter as tk
from tkinter import filedialog

import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.cm as cm

import numpy as np

import glob

import nibabel as nb

import math

def load_excel():

    global patient_overview, file_path

    file_path = filedialog.askopenfilename()
    patient_overview = pd.read_excel(file_path)

    app.Patients = list(patient_overview['Patient'])
    app.Patient = app.Patients.pop(0)
    while not isinstance(app.Patient,str):
        app.Patient = app.Patients.pop(0)
    view_pat()

def view_pat():

    img_path = app.Patient+'/img-nii/*.nii.gz'
    first_img = glob.glob(img_path)[0]
    if hasattr(app,'image'):
        del app.image


    if os.path.isfile(first_img):
        print('Loading...')
        plot1.title.set_text(f'Loading {os.path.basename(app.Patient)}...')
        canvas.draw()
        image_file = nb.load(first_img)
        app.image = image_file.get_fdata()

    current_CNR = patient_overview.loc[patient_overview['Patient']==app.Patient, 'CNR'].values[0]
    print(app.Patient)
    print(current_CNR)
    if math.isnan(current_CNR):
        current_CNR = 'None'
    app.to_view = int((50)/100 * app.image.shape[2])
    visualizer = app.image[:,:,app.to_view]
    #visualizer = visualizer.resize((220,220))
    #app.photo = ImageTk.PhotoImage(image = Image.fromarray(visualizer))
    plot1.clear()
    plot1.imshow(visualizer[:,:], cmap = cm.Greys_r)
    plot1.title.set_text(f'{os.path.basename(app.Patient)} with CNR: {current_CNR}')
    canvas.draw()
    
    if not app.scale_loaded:
        app.scale = tk.Scale(master=frame, orient='vertical',from_=1, to=100, resolution=1,
                  showvalue=False, command=next_img)
        app.scale.set(50)
        app.scale.pack(side = 'left',fill='y')
        canvas.get_tk_widget().pack()
        app.scale_loaded = True

def next_pat():
    app.Patient = app.Patients.pop(0)
    while not isinstance(app.Patient,str):
        app.Patient = app.Patients.pop(0)
        if not app.Patient:
            tkinter.messagebox.showerror(title='Error', message='No more patients in spreadsheet', **options)
            return

    view_pat()

def next_img(i):
    app.to_view = int((int(i)-1)/100 * app.image.shape[2])
    visualizer = app.image[:,:,app.to_view]
    plot1.imshow(visualizer, cmap = cm.Greys_r)
    canvas.draw()

def select_spot(event):

    if in_pt_mode_var.get() == 'on':

        confirm_button.place(relx=0.35, rely=0.85, anchor='center')
        delete_pts_button.place(relx=0.35, rely=0.9, anchor='center')
        
        x, y = event.x, event.y

        if x > 130 and x < 500 and y < 430 and y > 60:

            x2 = (x - 130)*(500/370)
            y2 = (y - 60)*(500/370)

            if pt_option.get() == 'Blood Pool':
                #convert to where that sits on canvas
                app.blood_pool_pts.append([x2,y2])
                plot1.scatter(x2,y2,color='red')
                canvas.draw()

            elif pt_option.get() == 'Myocardium':
                app.myo_pts.append([x2,y2])
                plot1.scatter(x2,y2,color='blue')
                canvas.draw()

def use_points():
    print('Calculating CNR')
    CNR = get_CNR(app.image,app.blood_pool_pts, app.myo_pts,app.to_view)
    patient_overview.loc[patient_overview['Patient']==app.Patient, 'CNR'] = CNR

    app.blood_pool_pts = []
    app.myo_pts = []

    suffix = ' with CNR'
    if suffix in file_path:
        save_path = file_path

    else:
        z = file_path.split('.')
        save_path = z[0]+suffix +'.'+z[1]

    patient_overview.to_excel(save_path)

    #plot1.clf()
    plot1.clear()
    visualizer = app.image[:,:,app.to_view]
    plot1.imshow(visualizer[:,:], cmap = cm.Greys_r)
    plot1.title.set_text(f'CNR: {CNR}')
    canvas.draw()

def redo_points():

    #fig.cla()
    #plot1 = fig.add_subplot(111)
    plot1.clear()
    visualizer = app.image[:,:,app.to_view]
    plot1.imshow(visualizer[:,:], cmap = cm.Greys_r)
    canvas.draw()
    app.blood_pool_pts = []
    app.myo_pts = []


def get_CNR(image_data,signal_pts,myo_pts,slicez,area_of_interest_radius = 8):
    
 #   plt.close()
    signal1 = []
    for signal_pt in signal_pts:
        xref = int(signal_pt[0])
        yref = int(signal_pt[1])


        # Note: the indexing is backwards for x and y 
        signal1.append(image_data[yref-area_of_interest_radius:yref+area_of_interest_radius,
                             xref-area_of_interest_radius:xref+area_of_interest_radius,
                             slicez])

    signal1_mean = np.mean( np.array(signal1))

    signal2 = []
    for myo_pt in myo_pts:

        xref = int(myo_pt[0])
        yref = int(myo_pt[1])

        signal2.append(image_data[yref-area_of_interest_radius:yref+area_of_interest_radius,
                   xref-area_of_interest_radius:xref+area_of_interest_radius,
                   slicez])

    signal2_std = np.std(signal2)
    signal2_mean = np.mean( np.array(signal2))

    CNR = abs(signal1_mean - signal2_mean)/signal2_std
    return CNR


def place_holder():
    pass

app = tk.Tk()

app.geometry("700x600")

app.title("CNR Analyzer")

app.scale_loaded = False

frame = tk.Frame(app, width=200, height=200)
frame.pack(padx = 30, pady = 10, fill='both')

fig = Figure()
plot1 = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=frame)

full_width = 515 - 120
full_height = 430 - 60

print(full_width,full_height)

app.blood_pool_pts = []
app.myo_pts = []

button_width = 9

load_button = tk.Button(text='Load xlsx', command = load_excel, width = button_width)
load_button.place(relx = 0.15, rely=0.85, anchor = 'center')

next_button = tk.Button(text='Next patient', command = next_pat, width = button_width)
next_button.place(relx=0.15, rely=0.9, anchor='center')

confirm_button = tk.Button(text="Analyze points", command = use_points, width = button_width)#, command = accept_points)
delete_pts_button = tk.Button(text="Redo points", command = redo_points, width = button_width)#, command = delete_points)

pt_option = tk.StringVar(app)
in_pt_mode_var = tk.StringVar(app, 'off')

in_pt_mode = tk.Radiobutton(app, text='Selection Mode', variable=in_pt_mode_var, value='on', width = button_width+5)
in_pt_mode.place(relx = 0.55, rely=0.9, anchor='center')

in_pt_mode = tk.Radiobutton(app, text='View Mode', variable=in_pt_mode_var, value='off', width = button_width+5)
in_pt_mode.place(relx = 0.55, rely=0.85, anchor='center')

point_type = tk.OptionMenu(app, pt_option, 'Blood Pool','Myocardium')
point_type.place(relx=0.75, rely=0.87, anchor='center')


app.bind('<ButtonRelease-1>', select_spot)

app.mainloop()

