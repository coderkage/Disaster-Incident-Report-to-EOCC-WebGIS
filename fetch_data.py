from koboextractor import KoboExtractor
import json, requests, base64
import pandas as pd
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox
from tkcalendar import DateEntry
from tkinter import ttk
import os

def submit_login():

    # Check if all fields are filled
    for field_label, field_widget in fields:
        if isinstance(field_widget, DateEntry):
            if not field_widget.get_date():
                messagebox.showwarning("Warning", f"Please fill in {field_label.strip(':')}.")
                return
        else:
            if not field_widget.get():
                messagebox.showwarning("Warning", f"Please fill in {field_label.strip(':')}.")
                return
    username = fields[0][1].get()
    password = fields[1][1].get()
    start_date = fields[2][1].get_date()
    start_time = fields[3][1].get()
    end_date = fields[4][1].get_date()
    end_time = fields[5][1].get()

    # Constructing start and end date-time objects
    start_datetime = datetime.combine(start_date, datetime.strptime(start_time, "%H:%M").time())
    end_datetime = datetime.combine(end_date, datetime.strptime(end_time, "%H:%M").time())

    # Convert start and end date-time objects to strings matching the format in the DataFrame
    start_datetime_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    end_datetime_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    
    #access your kobo account using your token
    your_token = 'fc2a87b44c2c5dac8d01b3bb2c2ea2ea33258028' #Replace by your token
    kobo = KoboExtractor(your_token, 'https://kf.kobotoolbox.org/api/v2')

    #access data submitted to a specific form using the form id
    form_id = 'a4q35bVsHRXsS6nyF4YcHY' #Replace by your Form ID
    data = kobo.get_data(form_id, query=None, start=None, limit=None, submitted_after=None)

    df = pd.json_normalize(data['results'])

    df['Geographical_Coordin_the_Hazard_Incident'] = df['Geographical_Coordin_the_Hazard_Incident'].fillna('0 0 0 0')

    df[['latitude', 'longitude', 'altitude', 'accuracy']] = df['Geographical_Coordin_the_Hazard_Incident'].str.split(' ', expand=True)

    df[['latitude', 'longitude', 'altitude', 'accuracy']] = df[['latitude', 'longitude', 'altitude', 'accuracy']].apply(pd.to_numeric)

    filtered_df = df[(df['start'] >= start_datetime_str) & (df['end'] <= end_datetime_str)]

    # If there are no matching records, show a message box
    if filtered_df.empty:
        messagebox.showinfo("Info", "No records found for the selected date-time range.")
        return


    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    folder_name = f'data_{timestamp}'
    os.makedirs(folder_name, exist_ok=True)

    # Save the filtered DataFrame to CSV within the folder
    file_name = os.path.join(folder_name, f'data_{timestamp}.csv')
    filtered_df.to_csv(file_name, index=False)



    # csv_file = "coordinate_iraq_iran.csv"
    gdf = gpd.read_file(file_name)

    gdf['geometry'] = gdf.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)

    # Set the CRS (Coordinate Reference System) for the GeoDataFrame
    # Replace "epsg:4326" with the appropriate EPSG code for your data
    gdf.crs = "epsg:4326"

    output_shapefile = os.path.join(folder_name, f'DIR_{timestamp}.shp')
    gdf.to_file(output_shapefile, driver='ESRI Shapefile', encoding='utf-8')


    credentials = f'{username}:{password}'

    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    authorization_header_value = f'Basic {encoded_credentials}'

    url = "http://180.211.110.22/api/v2/uploads/upload"


    files = [
        ('base_file', (os.path.join(folder_name, f'DIR_{timestamp}.shp'), open(os.path.join(folder_name, f'DIR_{timestamp}.shp'), 'rb'), 'application/octet-stream')),
        ('dbf_file', (os.path.join(folder_name, f'DIR_{timestamp}.dbf'), open(os.path.join(folder_name, f'DIR_{timestamp}.dbf'), 'rb'), 'application/octet-stream')),
        ('shx_file', (os.path.join(folder_name, f'DIR_{timestamp}.shx'), open(os.path.join(folder_name, f'DIR_{timestamp}.shx'), 'rb'), 'application/octet-stream')),
        ('prj_file', (os.path.join(folder_name, f'DIR_{timestamp}.prj'), open(os.path.join(folder_name, f'DIR_{timestamp}.prj'), 'rb'), 'application/octet-stream'))
    ]

    headers = {
        'Authorization': authorization_header_value
    }

    response = requests.request("POST", url, headers=headers, files=files)
    if response.status_code == 201:
        print(f"status code {response.status_code}")
        print("dataset uploaded successfully!")
        messagebox.showinfo("Success", "XLS & shapefile created successfully. \nExported to EOCC Dashboard.")

    
    
def check_completion():
    # Check if all fields are filled
    for field_label, field_widget in fields:
        if isinstance(field_widget, DateEntry):
            if not field_widget.get_date():
                return False
        else:
            if not field_widget.get():
                return False
    return True

def on_closing():
    # if not check_completion():
    #     messagebox.showerror("Error", "Please fill all details before closing the window.")
    #     return
    root.destroy()

now = datetime.now()
yesterday = now - timedelta(days=1)

root = tk.Tk()
root.title("Disaster Incident Report (DIR) to EOCC WebGIS")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Center the window
window_width = 425
window_height = 325
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height/2 - window_height/2)
position_right = int(screen_width/2 - window_width/2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

# Apply styles
root.configure(bg='lightblue')
entry_font = ('Calibri', 12)
label_font = ('Calibri', 12, 'bold')

tk.Label(root, text="Select range to export DIR to EOCC WebGIS", bg='lightblue', font=('Helvetica', 10, 'bold')).grid(row=0, columnspan=2, pady=10, padx=25)

time_options = [f'{h:02d}:{m:02d}' for h in range(24) for m in (0, 30)]

# Labels and Entry fields
fields = [
    ("Username:", tk.Entry(root, font=entry_font)),
    ("Password:", tk.Entry(root, show='*', font=entry_font)),
    ("Start Date:", DateEntry(root, font=entry_font, width=17, background='darkblue', foreground='white', borderwidth=2, year=yesterday.year, month=yesterday.month, day=yesterday.day)),
    ("Start Time:", ttk.Combobox(root, font=entry_font, values=time_options, width=17)),
    ("End Date:", DateEntry(root, font=entry_font, width=17, background='darkblue', foreground='white', borderwidth=2, year=now.year, month=now.month, day=now.day)),
    ("End Time:", ttk.Combobox(root, font=entry_font, values=time_options, width=17))
]

# Set default values for start and end times
fields[3][1].set(yesterday.strftime('%H:%M'))  # Start Time
fields[5][1].set(now.strftime('%H:%M'))       # End Time

# Iterate through fields and place them
for idx, (label, entry) in enumerate(fields, start=1):
    tk.Label(root, text=label, bg='lightblue', font=label_font, anchor='w').grid(row=idx, column=0, padx=60, pady=5, sticky='w')
    entry.grid(row=idx, column=1, padx=5, pady=5)

# Submit button
submit_button = tk.Button(root, text="Export", command=submit_login, font=('Calibri', 12, 'bold'), bg='blue', fg='white')
submit_button.grid(row=13, columnspan=2, pady=20, padx=70)

root.mainloop()

