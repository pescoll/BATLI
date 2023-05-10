from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import os
import json
import time
import matplotlib
matplotlib.use('Agg')
from werkzeug.utils import secure_filename
import urllib.parse

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'csv', 'txt'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = '/Users/pedro/Documents/GitHub/backward_analysis/'

def clean_dataframe(df, database_info):
    population = database_info["Population"]
    prefix = population.replace("Population - ", "") + " - "
    
    df.columns = [c.replace(prefix, '').replace(' [µm]', '_um').replace('µm', 'um') if isinstance(c, str) else c for c in df.columns]

    # create a dictionary with old/new names
    col_names = {'Row'          : 'row',
                 'Column'       : 'col',
                 'Plane'        : 'plane',
                 'Timepoint'    : 't',
                 'Field'        : 'field',
                 'Object No'    : 'N',
                 'X'            : 'x',
                 'Y'            : 'y', 
                 'Bounding Box' : 'bbox',
                 'Position X_um': 'pos_x_um',
                 'Position Y_um': 'pos_y_um',
                 'Bacteria'     : 'bact',
                 'Track Point X': 'track_point_x',
                 'Track Point Y': 'track_point_y',
                 'Age [s]'      : 'age_s',
                 'Current Displacement X_um': 'disp_x_um',
                 'Current Displacement Y_um': 'disp_y_um',
                 'Current Speed [um/s]'     : 'speed_um_s',
                 'Number of Legio- per Cell '      : 'leg_n',
                 'Legio Area [µm²]- Sum per Cell ' : 'leg_area',
                 'SER TMRM SER Edge 0.535331905782 um' : 'mito_frag',
                 'SD/Mean TMRM'    : 'tmrm_sdmean',
                 'Intensity AnnexinV-647 Mean' :'annexin_mfi', 
                 'Intensity Nucleus HOECHST 33342 Mean' : 'hoechst_mfi',
                 'Number of Legio- per Cell '      : 'leg_n',
                 'Legio Area [µm²]- Sum per Cell ' : 'leg_area',
                 'Infected'        : 'infected'
                }

    # rename the columns
    df = df.rename(columns = col_names)

    # add a unique well ID
    df['well_id'] = -1  
    rows = df['row'].unique()   
    cols = df['col'].unique() 

    _well_id = 0
    for ri, _r in enumerate(rows):
        for ci, _c in enumerate(cols):
            inds = (df['row'] == _r) & (df['col'] == _c) 
            _well_id += 1 
            df.loc[inds, 'well_id'] = _well_id

    # create unique cell id
    gr = df.groupby(['well_id', 'field', 'N'])

    # Initialize an empty list to store all subsets.
    dfs_to_concat = []

    for k, v in gr.groups.items():
        w, f, c = k
        _df = df.loc[v].sort_values('t')
        try:
            _cell_id = 'w%d_f%d_c%d' % (w, int(f), int(c))  # Convert f and c to integers
        except ValueError:
            print(f"Could not convert {f} or {c} to integer.")
            continue
        _df['cell_lbl'] = _cell_id

        # Append this subset to the list of dataframes to concatenate.
        dfs_to_concat.append(_df)  

        # Concatenate all dataframes in the list after the loop.
        cells_df = pd.concat(dfs_to_concat) 
    
    return cells_df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load_dataset', methods=['POST'])
def load_dataset():
    print("load_dataset() called")
    if 'file' not in request.files:
        return 'No file provided', 400

    file = request.files['file']
    start_time = time.time()
    if file.filename == '':
        return 'No file selected', 400

    # Read the file into a DataFrame
    print("Reading file into DataFrame")
    database_info = {}
    data = []
    with open(file.filename, 'r') as f:
        for i, line in enumerate(f):
            if 1 <= i <= 6:
                split_line = line.strip().split('\t')
                if len(split_line) != 2:
                    continue
                key, value = split_line
                database_info[key] = value
            elif i > 8:
                data.append(line.strip().split('\t'))

    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Generate the database_info file name
    database_info_name = f"database_info_{database_info['Plate Name']}_{database_info['Measurement']}_{database_info['Evaluation']}_{database_info['Population']}.csv"

    with open(database_info_name, 'w') as f:
        json.dump(database_info, f)

    # Clean the DataFrame
    cells_df = clean_dataframe(df, database_info)
    create_plot(cells_df)
    end_time = time.time()
    elapsed_time = end_time - start_time
    plot_url = create_plot(cells_df)

    # Convert the elapsed time to hours, minutes, and seconds
    m, s = divmod(elapsed_time, 60)
    h, m = divmod(m, 60)

    elapsed_time_str = f"{int(h)}h, {int(m)}m, {int(s)}s"

    # Generate the cleaned dataset file name
    cleaned_dataset_name = f"cleaned_dataset_{database_info['Plate Name']}_{database_info['Measurement']}_{database_info['Evaluation']}_{database_info['Population']}.csv"

    # Save the cleaned dataset as a CSV file
    print("Saving cleaned dataset")
    cells_df.to_csv(cleaned_dataset_name, index=False)

    # Calculate the required values
    number_of_wells = cells_df['well_id'].nunique()
    number_of_timepoints = cells_df['t'].nunique()
    number_of_cells = cells_df['cell_lbl'].nunique()

    response = {
        'message': 'Dataset successfully loaded and cleaned',
        'database_info': database_info,
        'number_of_wells': len(cells_df['well_id'].unique()),
        'number_of_timepoints': len(cells_df['t'].unique()),
        'number_of_cells': len(cells_df['cell_lbl'].unique()),
        'elapsed_time': elapsed_time_str,
        'plot_url': plot_url
    }

    return jsonify(response)

def create_plot(cells_df):
    wells = cells_df['well_id'].unique()
    cell_counts = [len(cells_df[cells_df['well_id'] == well]['cell_lbl'].unique()) for well in wells]

    plt.figure(figsize=(10, 6))
    plt.bar(wells, cell_counts, color=plt.cm.rainbow(np.linspace(0, 1, len(wells))))
    plt.xlabel('well_id')
    plt.ylabel('number of cell_lbl')
    plt.title('Number of unique cells per well')
    plot_path = 'static/plot.png'
    plt.savefig(plot_path)
    return plot_path

@app.route('/load_cleaned_dataset', methods=['POST'])
def load_cleaned_dataset():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    filename = urllib.parse.unquote(filename)  # decode URL encoded characters
    
    if file.filename == '':
        return jsonify({'message': 'No file selected for uploading'}), 400
    if not allowed_file(file.filename):
        return jsonify({'message': 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'}), 400

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    # Remove 'cleaned_' prefix from filename
    if filename.startswith("cleaned_"):
        filename = filename[8:]

    db_info_filename = 'database_info_' + filename
    db_info_path = os.path.join(app.config['UPLOAD_FOLDER'], db_info_filename)
    db_info_path = urllib.parse.unquote(db_info_path)  # decode URL encoded characters
    
    with open(db_info_path, 'r') as f:
        db_info = json.load(f)
    
    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    create_plot(cells_df)
    
    response = {
        'message': 'Dataset loaded successfully',
        'database_info': db_info,
        'number_of_wells': len(cells_df['well_id'].unique()),
        'number_of_timepoints': len(cells_df['timepoint'].unique()),
        'number_of_cells': len(cells_df['cell_lbl'].unique()),
        'elapsed_time': 'N/A',
        'plot_url': url_for('get_plot')
    }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True)
