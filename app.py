from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, send_file, abort
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import io
from io import BytesIO
import base64
import os
import json
import time
import matplotlib
matplotlib.use('Agg')
from werkzeug.utils import secure_filename
import urllib.parse
import glob
from collections import OrderedDict
import datetime
import shutil


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'csv', 'txt', 'json'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

current_filename = None

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'user_data/'

def clean_dataframe(df, database_info):  # Basic cleaning and creation of unique well IDs and unique cell IDs
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
                 'Track Point X': 'track_point_x',
                 'Track Point Y': 'track_point_y',
                 'Age [s]'      : 'age_s',
                 'Current Displacement X_um': 'disp_x_um',
                 'Current Displacement Y_um': 'disp_y_um',
                 'Current Speed [um/s]'     : 'speed_um_s'
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

    # # Previous code Dmitry:
    # # Assign unique cell labels to each row in one line
    # df['cell_lbl'] = 'w' + df['well_id'].astype(str) + '_f' + df['field'].astype(str) + '_c' + df['N'].astype(str)
    # # Sort values by 'cell_lbl' and 't' as before
    # df.sort_values(['cell_lbl', 't'], inplace=True)
    # # First, create the 'cell_lbl' column as before
    # df['cell_lbl'] = 'w' + df['well_id'].astype(str) + '_f' + df['field'].astype(str) + '_c' + df['N'].astype(str)
    # # Now group by 'cell_lbl'
    # groups = df.groupby('cell_lbl')
    # # For each group, sort by 't', then collect all groups back into a list of dataframes
    # dfs_sorted = [group.sort_values('t') for _, group in groups]
    # # Now concatenate all the sorted dataframes back together in one step, respecting the original order
    # df = pd.concat(dfs_sorted)

    # First, create the 'cell_lbl' column as before
    df['cell_lbl'] = 'w' + df['well_id'].astype(str) + '_f' + df['field'].astype(str) + '_c' + df['N'].astype(str)

    # Now group by 'cell_lbl'
    groups = df.groupby('cell_lbl')

    # Make an ordered percentage and sort by time for each group
    ordered_groups = OrderedDict((name, wet.sort_values(by='t')) for name, wet in groups)

    # Concatenate all the sorted dataframes back together in one step
    cells_df = pd.concat(ordered_groups.values())

    # Substitute NaN with an empty string
    cells_df = cells_df.fillna('')

    # Replace non-alphanumeric characters (excluding periods and underscores) in string values with underscores
    cells_df.replace({r'[^a-zA-Z0-9_.-]': '_'}, regex=True, inplace=True)

    # Organize the table
    cells_df = cells_df.sort_values(['well_id', 't'])

    # you can change 'cell_lbl' to be the index if needed, by doing this:
    # df.set_index('cell_lbl', inplace=True)
    # and if you still need to sort and split the DataFrame into smaller dataframes, you can use:
    # dfs_to_concat = [group.sort_values('t') for _, group in df.groupby('cell_lbl')]

    # OLD CODE DMITRY:
    # # create unique cell id
    # gr = df.groupby(['well_id', 'field', 'N'])
    # # Initialize an empty list to store all subsets.
    # dfs_to_concat = []
    # for k, v in gr.groups.items():
    #     w, f, c = k
    #     _df = df.loc[v].sort_values('t')
    #     try:
    #         _cell_id = 'w%d_f%d_c%d' % (w, int(f), int(c))  # Convert f and c to integers
    #     except ValueError:
    #         print(f"Could not convert {f} or {c} to integer.")
    #         continue
    #     _df['cell_lbl'] = _cell_id

    #     # Append this subset to the list of dataframes to concatenate.
    #     dfs_to_concat.append(_df)  

    #     # Concatenate all dataframes in the list after the loop.
    #     cells_df = pd.concat(dfs_to_concat)

    #     print(_cell_id)

    print(cells_df.columns)  # print column names before the operation
    cells_df.columns = cells_df.columns.str.lower().str.replace(' ', '_')
    print(cells_df.columns)  # print column names after the operation

    return cells_df


@app.route('/')
def index():
    return render_template('loader.html')

@app.route('/computed_data/plots/<path:path>')
def serve_plots(path):
    response = send_from_directory('computed_data/plots', path)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/computed_data/tables/<path:path>')
def serve_tables(path):
    response = send_from_directory('computed_data/tables', path)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/computed_data/backward/<path:path>')
def serve_backward(path):
    response = send_from_directory('computed_data/backward', path)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# CLEANER
@app.route('/cleaner')
def cleaner():
    return render_template('cleaner.html')

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
    for i, line in enumerate(file.stream):
        if 1 <= i <= 6:
            split_line = line.decode().strip().split('\t')
            if len(split_line) != 2:
                continue
            key, value = split_line
            database_info[key] = value
        elif i > 8:
            data.append(line.decode().strip().split('\t'))

    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Generate the database_info file name
    dataset_info_name = f"dataset_info_{database_info['Plate Name']}_{database_info['Measurement']}_{database_info['Evaluation']}_{database_info['Population']}.json"
    dataset_info_name = dataset_info_name.replace(' ', '_')
    print(database_info)

    with open('./user_data/' + dataset_info_name, 'w') as f:
        json.dump(database_info, f)

    # Clean the DataFrame
    cells_df = clean_dataframe(df, database_info)
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Convert the elapsed time to hours, minutes, and seconds
    m, s = divmod(elapsed_time, 60)
    h, m = divmod(m, 60)

    elapsed_time_str = f"{int(h)}h, {int(m)}m, {int(s)}s"

    # Generate the cleaned dataset file name
    cleaned_dataset_name = f"cleaned_dataset_{database_info['Plate Name']}_{database_info['Measurement']}_{database_info['Evaluation']}_{database_info['Population']}.csv"
    cleaned_dataset_name = cleaned_dataset_name.replace(' ', '_')

    # Save the cleaned dataset as a CSV file
    print("Saving pre-processed dataset")
    cells_df.to_csv('./user_data/' + cleaned_dataset_name, index=False)

    response = {
        'message': 'Dataset was loaded and pre-processed',
        'database_info': database_info,
        'number_of_wells': len(cells_df['well_id'].unique()),
        'number_of_timepoints': len(cells_df['t'].unique()),
        'number_of_cells': len(cells_df['cell_lbl'].unique()),
        'elapsed_time': elapsed_time_str,
    }
    print(response)

    # Update the response with the cleaned dataset filename
    response.update({
    "cleaned_dataset_file": cleaned_dataset_name,
    "filename": cleaned_dataset_name
    })

    response = jsonify(response)
    response.headers['Content-Type'] = 'application/json'
    print(response)
    return response

@app.route('/get_column_names', methods=['POST'])
def get_column_names():
    data = request.get_json()
    filename = data.get('filename')

    if not filename:
        return jsonify({'message': 'Missing filename parameter'}), 400

    df = pd.read_csv('./user_data/' + filename)
    column_names = df.columns.tolist()
    print(type(column_names))  # check the type of column_names
    print(column_names)  # log the column names
    return jsonify(column_names)

@app.route('/rename_columns', methods=['POST'])
def rename_columns():
    data = request.get_json()

    filename = data.get('filename')
    mappings = data.get('mappings')
    deletes = data.get('deletes')

    if not filename or not mappings:
        return jsonify({'message': 'Missing filename or mappings parameter'}), 400

    try:
        df = pd.read_csv('./user_data/' + filename)

        # Drop columns
        if deletes:
            df.drop(columns=deletes, inplace=True)

        df.rename(columns=mappings, inplace=True)
        df.to_csv('./user_data/' + filename, index=False)

        # Save the mappings as a json file
        with open('./user_data/new_param_' + filename, 'w') as file:
            json.dump(mappings, file)

        return jsonify({'message': 'Columns renamed successfully'})

    except FileNotFoundError:
        return jsonify({'message': f'File not found: {filename}'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# LOADER

@app.route('/loader')
def loader():
    return render_template('loader.html')

@app.route('/load_cleaned_dataset', methods=['POST'])
def load_cleaned_dataset():
    print("load_cleaned_dataset() called")
    global current_filename
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected for uploading'}), 400
    if not allowed_file(file.filename):
        return jsonify({'message': 'Allowed file types are txt, csv, json'}), 400

    # Save the file first
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Decode URL encoded characters in the filename
    filename = urllib.parse.unquote(filename)
    current_filename = filename

    # Replace 'cleaned_dataset_' prefix with 'dataset_info_' in filename
    filename_without_ext, _ = os.path.splitext(filename)
    db_info_filename = filename_without_ext.replace('cleaned_dataset_', 'dataset_info_') + '.json'
    db_info_path = os.path.join(app.config['UPLOAD_FOLDER'], db_info_filename)

    # Decode URL encoded characters in the db_info_path
    db_info_path = urllib.parse.unquote(db_info_path)

    # Load the database info
    with open(db_info_path, 'r') as f:
        db_info = json.load(f)

    # Load the cleaned dataset into a DataFrame
    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    print("Reading file into DataFrame")

    # Delete old plot files
    for plot_file in glob.glob('computed_data/plots/*.png'):
        os.remove(plot_file)    

    # Delete old tables files
    for table_file in glob.glob('computed_data/tables/*.csv'):
        os.remove(table_file)    

    # Create the plot
    wells = cells_df['well_id'].unique()
    cell_counts = [len(cells_df[cells_df['well_id'] == well]['cell_lbl'].unique()) for well in wells]
    timestamp = int(time.time())
    plt.figure(figsize=(10, 6))
    plt.bar(wells, cell_counts, color=plt.cm.rainbow(np.linspace(0, 1, len(wells))))
    plt.xlabel('well_id')
    plt.ylabel('number of cell_lbl')
    plt.title('Number of unique tracked cells per well')
    plot1_path = f"summary_plot_cells_per_well_{db_info['Plate Name']}_{timestamp}.png"
    plt.savefig('computed_data/plots/' + plot1_path)
    print('computed_data/plots/' + plot1_path)

    response = {
        'message': 'Dataset loaded successfully',
        'database_info': db_info,
        'number_of_wells': len(cells_df['well_id'].unique()),
        'number_of_timepoints': len(cells_df['t'].unique()),
        'number_of_cells': len(cells_df['cell_lbl'].unique()),
        'plot1_url': url_for('serve_plots', path=plot1_path)
    }

    return jsonify(response), 200

@app.route('/get_first_rows', methods=['GET'])
def get_first_rows():
    filename = request.args.get('filename')

    if not filename:
        return jsonify({'message': 'Missing filename parameter'}), 400

    cleaned_dataset_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(cleaned_dataset_path)

    if not os.path.exists(cleaned_dataset_path):
        return jsonify({'message': 'File not found'}), 404

    df = pd.read_csv(cleaned_dataset_path, nrows=20)
    df = df.fillna('NaN')
    response = {
        'headers': list(df.columns),
        'first_rows': df.to_dict(orient='records'),
    }
    
    return jsonify(response), 200

# VIEWER
@app.route('/viewer')
def viewer():
    return render_template('viewer.html')

@app.route('/get_parameter_names', methods=['GET'])
def get_parameter_names():
    if current_filename is None:
        return jsonify({'message': 'No file loaded'}), 400
    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], current_filename))
    conditions_cols = ['bacteria', 'bact', 'compound', 'treatment', 'pretreatment', 'assay', 'assays', 'assay_number'] # list of conditions columns
    condition_cols = [col for col in conditions_cols if col in cells_df.columns]
    column_names = cells_df.select_dtypes(include=[np.number]).columns.tolist()
    print(condition_cols)
    print(column_names)
    return jsonify({'condition_cols': condition_cols, 'column_names': column_names}), 200

@app.route('/plot2', methods=['POST'])
def plot2():
    global current_filename
    if current_filename is None:
        return jsonify({'message': 'No file loaded'}), 400

    data = request.get_json()
    selected_condition = data['condition']
    selected_second_condition = data.get('secondCondition')  # This will be None if not provided
    selected_parameter = data['parameter']
    percentage = int(data['percentage'])

    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], current_filename))

    # Delete old plot files
    for plot_file in glob.glob('computed_data/plots/plot_*.png'):
        os.remove(plot_file)    

    # Delete old tables files
    for table_file in glob.glob('computed_data/tables/table_*.csv'):
        os.remove(table_file)   

    # Find the global minimum and maximum 't' values
    t_min = cells_df['t'].min()
    t_max = cells_df['t'].max()

    yMin = data.get('yMin')
    yMax = data.get('yMax')

    if yMin is not None:
        yMin = float(yMin)
    if yMax is not None:
        yMax = float(yMax)

    # Find the total number of unique 't' values in the dataframe
    total_timepoints = len(cells_df['t'].unique())
    required_timepoints = total_timepoints * percentage // 100

    # Define a function to test if a cell_lbl's track length is above the required threshold
    def test_length(x):
        return len(x) >= required_timepoints

    print("Total timepoints: ", total_timepoints)
    print("Required timepoints: ", required_timepoints)

    # Filter the dataframe to only include cell_lbl's that pass the test_length function
    filtered_cells_df = cells_df[cells_df.groupby('cell_lbl')['t'].transform(test_length)].copy()
    
    print("Number of unique cell_lbl in original df: ", len(cells_df['cell_lbl'].unique()))
    print("Number of unique cell_lbl in filtered df: ", len(filtered_cells_df['cell_lbl'].unique()))
    
    sub_df = filtered_cells_df[selected_condition].unique()

    float('inf')  # Returns: inf
    float('-inf')  # Returns: -inf

    plot_urls = []

    try:
        if selected_second_condition and selected_second_condition != 'none':
            condition_combinations = filtered_cells_df[[selected_condition, selected_second_condition]].drop_duplicates().values.tolist()
        else:
            condition_combinations = [(value,) for value in filtered_cells_df[selected_condition].unique()]

        print(f"Condition combinations: {condition_combinations}")  # print to debug

        for condition_values in condition_combinations:
            if len(condition_values) == 2:
                _df = filtered_cells_df[(filtered_cells_df[selected_condition] == condition_values[0]) & (filtered_cells_df[selected_second_condition] == condition_values[1])]
                num_cells = len(_df['cell_lbl'].unique())
                plot_title = f"{condition_values[0]} - {condition_values[1]} (n = {num_cells} cells)"  # Set the plot title with both condition values
            elif len(condition_values) == 1:
                _df = filtered_cells_df[filtered_cells_df[selected_condition] == condition_values[0]]
                num_cells = len(_df['cell_lbl'].unique())
                plot_title = f"{condition_values[0]} (n = {num_cells} cells)"  # Set the plot title with only one condition value
            else:
                continue  # if there are no conditions, continue to the next iteration

            _df = _df.copy()
            _df['t'] = _df['t'].astype(int)
            _df.sort_values(by=['cell_lbl', 't'], inplace=True)  # Sort by 'cell_lbl' and 't'

            fig, ax = plt.subplots(figsize=(12, 4))  # New figure for each condition

            ax.set_title(plot_title)
            ax.set_ylabel(selected_parameter)
            ax.set_xlabel('time')
            if yMin is not None and yMax is not None:
                ax.set_ylim(yMin, yMax)

            normalization = data['normalization']

            if normalization == 't0':
                # Normalize the data to t=0
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    t0_value = group.loc[group['t'].idxmin(), selected_parameter]
                    group[selected_parameter] /= t0_value
                    _df.loc[group.index, selected_parameter] = group[selected_parameter]
                    # if t0_value == 0:
                    #     t0_value = 1e-10  # Substitute a small positive number for t0_value
                    # group[selected_parameter] /= t0_value
                    # _df.loc[group.index, selected_parameter] = group[selected_parameter]
            
            # Normalize custom
            elif normalization == 'custom':
                range_start = int(data.get('range_start', 0))
                range_end = int(data.get('range_end', 4))

                for cell_lbl, group in _df.groupby('cell_lbl'):
                    average_value = group[(group['t'] >= range_start) & (group['t'] <= range_end)][selected_parameter].mean()
                    if average_value != 0:  # Avoid division by zero
                        group[selected_parameter] /= average_value
                        _df.loc[group.index, selected_parameter] = group[selected_parameter]

                # Delta normalization
                # elif normalization == 'delta':
                #     for cell_lbl, group in _df.groupby('cell_lbl'):
                #         group[selected_parameter] = group[selected_parameter] / group[selected_parameter].shift(1)
                #         _df.loc[group.index, selected_parameter] = group[selected_parameter]

            elif normalization == 'delta':
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    group[selected_parameter] = group[selected_parameter].diff()
                    _df.loc[group.index, selected_parameter] = group[selected_parameter]


            # Set the x-axis limit for each plot
            ax.set_xlim(t_min, t_max)

            for k, v in _df.groupby('cell_lbl').groups.items():
                single_cell_df = _df.loc[v]  # Subset of data that has only one cell
                ax.plot(single_cell_df['t'], single_cell_df[selected_parameter], alpha=0.08)

            
            timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
            condition_names = '_'.join(str(condition) for condition in condition_values)
            plot2_path = f"plot_single_cells_{condition_names}_{current_filename}_{timestamp}.png"
            _df.to_csv(f"computed_data/tables/table_{plot2_path.split('.')[0]}.csv")
            plt.savefig('computed_data/plots/' + plot2_path)

            plot_urls.append(url_for('serve_plots', path=plot2_path))

    except Exception as e:
        app.logger.error(f'Error generating plot: {e}')
        return jsonify({'message': f'Error generating plot: {e}'}), 500

    response = {
        'message': 'Plots created successfully',
        'plot_urls': plot_urls  # Return multiple plot URLs
    }

    return jsonify(response), 200

@app.route('/download', methods=['GET'])
def download_results():
    try:
        # create a temporary directory
        os.makedirs('temp', exist_ok=True)

        # copy files to temporary directory
        shutil.copytree('computed_data/plots', 'temp/plots')
        shutil.copytree('computed_data/tables', 'temp/tables')

        # create timestamp
        timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")

        # create zip file
        shutil.make_archive(f'results_{timestamp}', 'zip', 'temp')

        # remove temporary directory
        shutil.rmtree('temp')

        return send_file(f'results_{timestamp}.zip',
                         mimetype='zip',
                         attachment_filename=f'results_{timestamp}.zip',
                         as_attachment=True)
    except FileNotFoundError:
        abort(404)


# BACKWARD ANALYSIS

@app.route('/backward')
def backward():
    return render_template('backward.html')

@app.route('/get_parameter_names_backward_1', methods=['GET'])
def get_parameter_names_backward_1():
    if current_filename is None:
        return jsonify({'message': 'No file loaded'}), 400
    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], current_filename))
    conditions_cols = ['bacteria', 'bact', 'compound', 'treatment', 'pretreatment', 'assay', 'assays', 'assay_number'] # list of conditions columns
    condition_cols = [col for col in conditions_cols if col in cells_df.columns]
    column_names = cells_df.select_dtypes(include=[np.number]).columns.tolist()
    print(condition_cols)
    print(column_names)
    return jsonify({'condition_cols': condition_cols, 'column_names': column_names}), 200

@app.route('/plot3', methods=['POST'])
def plot3():
    global current_filename
    if current_filename is None:
        return jsonify({'message': 'No file loaded'}), 400

    data = request.get_json()
    selected_condition = data['condition']
    selected_second_condition = data.get('secondCondition')  # This will be None if not provided
    selected_parameter = data['parameter']
    percentage = int(data['percentage'])
    threshold = float(data['threshold'])

    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], current_filename))

    # Delete old backward_plot files
    for backward_plot_file in glob.glob('computed_data/backward/plot_*.png'):
        os.remove(backward_plot_file)    

    # Delete old backward_tables files
    for backward_table_file in glob.glob('computed_data/backward/table_*.csv'):
        os.remove(backward_table_file)   

    # Find the global minimum and maximum 't' values
    t_min = cells_df['t'].min()
    t_max = cells_df['t'].max()

    yMin = data.get('yMin')
    yMax = data.get('yMax')

    if yMin is not None:
        yMin = float(yMin)
    if yMax is not None:
        yMax = float(yMax)

    # Find the total number of unique 't' values in the dataframe
    total_timepoints = len(cells_df['t'].unique())
    required_timepoints = total_timepoints * percentage // 100

    # Define a function to test if a cell_lbl's track length is above the required threshold
    def test_length(x):
        return len(x) >= required_timepoints

    print("Total timepoints: ", total_timepoints)
    print("Required timepoints: ", required_timepoints)

    # Filter the dataframe to only include cell_lbl's that pass the test_length function
    filtered_cells_df = cells_df[cells_df.groupby('cell_lbl')['t'].transform(test_length)].copy()
    
    print("Number of unique cell_lbl in original df: ", len(cells_df['cell_lbl'].unique()))
    print("Number of unique cell_lbl in filtered df: ", len(filtered_cells_df['cell_lbl'].unique()))
    
    sub_df = filtered_cells_df[selected_condition].unique()

    float('inf')  # Returns: inf
    float('-inf')  # Returns: -inf

    plot_urls_backward = []

    # lists that hold cells ids:
    class_1 = []      
    class_0 = []

    filtered_cells_df.sort_values(by=['cell_lbl', 't'], inplace=True)  # Sort by 'cell_lbl' and 't'

    # number of points to average (N), adjust if necessary, will be used to determine growth
    Np = 2

    # go over each cell:
    for lbl, gr in filtered_cells_df.groupby(['cell_lbl']):
        # times = gr['t'].values
        growth = gr[selected_parameter].values 
        # calculate Area change:
        # array[-N:] -> returns last N elements
        # array[0:N] -> returns first N elements
        dA = float(growth[-Np:].mean() - growth[0:Np].mean())
        if dA >= threshold:
            class_1.append( lbl )
            print(lbl, growth[-Np:].mean(), growth[0:Np].mean(), dA)
        else:
            class_0.append( lbl )

    # find indices of those cells that are in the list of RB cells
    inds = filtered_cells_df['cell_lbl'].isin( class_1 )

    # add column growth:
    filtered_cells_df['growth'] = 0 # 0 by default
    filtered_cells_df.loc[inds, 'growth'] = 1  # set to 1 those that are from rb_cells_lbl list
    filtered_cells_df.to_csv(f"computed_data/backward/table_single_cells_filtered.csv")
    print( 'Class_1 cells/total cells: %d / %d'%(len(class_1), len(class_1)+len(class_0)) )   

    try:
        if selected_second_condition and selected_second_condition != 'none':
            condition_combinations = filtered_cells_df[[selected_condition, selected_second_condition]].drop_duplicates().values.tolist()
        else:
            condition_combinations = [(value,) for value in filtered_cells_df[selected_condition].unique()]

        print(f"Condition combinations: {condition_combinations}")  # print to debug

        for condition_values in condition_combinations:
            if len(condition_values) == 2:
                _df = filtered_cells_df[(filtered_cells_df[selected_condition] == condition_values[0]) & (filtered_cells_df[selected_second_condition] == condition_values[1])]
                num_cells = len(_df['cell_lbl'].unique())
                num_class_1  = len(_df[_df['growth'] == 1]['cell_lbl'].unique())
                num_class_0 = len(_df[_df['growth'] == 0]['cell_lbl'].unique())          
                num_class_total = num_class_1+num_class_0
                percentage_class_1 = (num_class_1*100)/num_class_total
                percentage_class_1 = format(percentage_class_1, '.2f')
                plot_title = f"{condition_values[0]} - {condition_values[1]} (n = {num_cells} cells, class_1 = {num_class_1} of {num_class_total} cells - {percentage_class_1}%)"  # Set the plot title with both condition values
            elif len(condition_values) == 1:
                _df = filtered_cells_df[filtered_cells_df[selected_condition] == condition_values[0]]
                num_cells = len(_df['cell_lbl'].unique())
                num_class_1  = len(_df[_df['growth'] == 1]['cell_lbl'].unique())
                num_class_0 = len(_df[_df['growth'] == 0]['cell_lbl'].unique())                   
                num_class_total = num_class_1+num_class_0
                percentage_class_1 = (num_class_1*100)/num_class_total
                percentage_class_1 = format(percentage_class_1, '.2f')
                plot_title = f"{condition_values[0]} (n = {num_cells} cells, class_1 = {num_class_1} of {num_class_total} cells - {percentage_class_1}%)"  # Set the plot title with both condition values
            else:
                continue  # if there are no conditions, continue to the next iteration

            _df = _df.copy()
            _df['t'] = _df['t'].astype(int)
            _df.sort_values(by=['cell_lbl', 't'], inplace=True)  # Sort by 'cell_lbl' and 't'

            # growth_max = _df[selected_parameter].max()

            fig, ax = plt.subplots(figsize=(12, 4))  # New figure for each condition
            ax.set_title(plot_title)
            ax.set_ylabel(selected_parameter)
            ax.set_xlabel('time')
            if yMin is not None and yMax is not None:
                ax.set_ylim(yMin, yMax)


            normalization = data['normalization']

            if normalization == 't0':
                # Normalize the data to t=0
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    t0_value = group.loc[group['t'].idxmin(), selected_parameter]
                    group[selected_parameter] /= t0_value
                    _df.loc[group.index, selected_parameter] = group[selected_parameter]
                    # if t0_value == 0:
                    #     t0_value = 1e-10  # Substitute a small positive number for t0_value
                    # group[selected_parameter] /= t0_value
                    # _df.loc[group.index, selected_parameter] = group[selected_parameter]
            
            # Normalize custom
            elif normalization == 'custom':
                range_start = int(data.get('range_start', 0))
                range_end = int(data.get('range_end', 4))

                for cell_lbl, group in _df.groupby('cell_lbl'):
                    average_value = group[(group['t'] >= range_start) & (group['t'] <= range_end)][selected_parameter].mean()
                    if average_value != 0:  # Avoid division by zero
                        group[selected_parameter] /= average_value
                        _df.loc[group.index, selected_parameter] = group[selected_parameter]

                # Delta normalization
                # elif normalization == 'delta':
                #     for cell_lbl, group in _df.groupby('cell_lbl'):
                #         group[selected_parameter] = group[selected_parameter] / group[selected_parameter].shift(1)
                #         _df.loc[group.index, selected_parameter] = group[selected_parameter]

            elif normalization == 'delta':
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    group[selected_parameter] = group[selected_parameter].diff()
                    _df.loc[group.index, selected_parameter] = group[selected_parameter]


            # Set the x-axis limit for each plot
            ax.set_xlim(t_min, t_max)

    
            # select a subset of data for class_1 and class_0
            _df_class_1 = _df[_df['growth']==1]
            _df_class_0 = _df[_df['growth']==0]                

            for lbl, gr in _df_class_0.groupby('cell_lbl'):
                    ax.plot( gr['t'], gr[selected_parameter], 'b-', alpha=0.05)
  
            for lbl, gr in _df_class_1.groupby('cell_lbl'):
                    ax.plot( gr['t'], gr[selected_parameter], 'r-', alpha=0.5 ) 
            
            timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
            condition_names = '_'.join(str(condition) for condition in condition_values)
            plot3_path = f"plot_backward_classes_{condition_names}_{current_filename}_{timestamp}.png"
            _df.to_csv(f"computed_data/backward/table_{plot3_path.split('.')[0]}.csv")
            plt.savefig('computed_data/backward/' + plot3_path)

            plot_urls_backward.append(url_for('serve_backward', path=plot3_path))
            print(plot_urls_backward)

    except Exception as e:
        app.logger.error(f'Error generating plot: {e}')
        return jsonify({'message': f'Error generating plot: {e}'}), 500

    response = {
        'message': 'Plots created successfully',
        'plot_urls_backward': plot_urls_backward  # Return multiple plot URLs
    }

    return jsonify(response), 200

@app.route('/get_parameter_names_backward_2', methods=['GET'])
def get_parameter_names_backward_2():
    if current_filename is None:
        return jsonify({'message': 'No file loaded'}), 400
        # Read the dataframe
    filename = "table_single_cells_filtered.csv"
    directory = "computed_data/backward"
    path = os.path.join(directory, filename)
    cells_df = pd.read_csv(path)
    conditions_cols2 = ['bacteria', 'bact', 'compound', 'treatment', 'pretreatment', 'assay', 'assays', 'assay_number'] # list of conditions columns
    condition_cols2 = [col for col in conditions_cols2 if col in cells_df.columns]
    column_names2 = cells_df.select_dtypes(include=[np.number]).columns.tolist()
    print(condition_cols2)
    print(column_names2)
    return jsonify({'condition_cols': condition_cols2, 'column_names': column_names2}), 200

@app.route('/plot4', methods=['POST'])
def plot4():
    global current_filename
    if current_filename is None:
        return jsonify({'message': 'No file loaded'}), 400

    data = request.get_json()
    selected_condition = data['condition']
    selected_second_condition = data.get('secondCondition')  # This will be None if not provided
    selected_parameter = data['parameter']
    percentage = int(data['percentage'])

    # Read the dataframe
    filename = "table_single_cells_filtered.csv"
    directory = "computed_data/backward"
    path = os.path.join(directory, filename)

    cells_df = pd.read_csv(path)

    # Find the global minimum and maximum 't' values
    t_min = cells_df['t'].min()
    t_max = cells_df['t'].max()

    yMin = data.get('yMin')
    yMax = data.get('yMax')

    if yMin is not None:
        yMin = float(yMin)
    if yMax is not None:
        yMax = float(yMax)

    # Find the total number of unique 't' values in the dataframe
    total_timepoints = len(cells_df['t'].unique())
    required_timepoints = total_timepoints * percentage // 100

    # Define a function to test if a cell_lbl's track length is above the required threshold
    def test_length(x):
        return len(x) >= required_timepoints

    print("Total timepoints: ", total_timepoints)
    print("Required timepoints: ", required_timepoints)

    # Filter the dataframe to only include cell_lbl's that pass the test_length function
    filtered_cells_df = cells_df[cells_df.groupby('cell_lbl')['t'].transform(test_length)].copy()
    
    print("Number of unique cell_lbl in original df: ", len(cells_df['cell_lbl'].unique()))
    print("Number of unique cell_lbl in filtered df: ", len(filtered_cells_df['cell_lbl'].unique()))
    
    sub_df = filtered_cells_df[selected_condition].unique()

    float('inf')  # Returns: inf
    float('-inf')  # Returns: -inf

    plot_urls_backward = []

    try:
        if selected_second_condition and selected_second_condition != 'none':
            condition_combinations = filtered_cells_df[[selected_condition, selected_second_condition]].drop_duplicates().values.tolist()
        else:
            condition_combinations = [(value,) for value in filtered_cells_df[selected_condition].unique()]

        print(f"Condition combinations: {condition_combinations}")  # print to debug

        for condition_values in condition_combinations:
            if len(condition_values) == 2:
                _df = filtered_cells_df[(filtered_cells_df[selected_condition] == condition_values[0]) & (filtered_cells_df[selected_second_condition] == condition_values[1])]
                num_cells = len(_df['cell_lbl'].unique())
                num_class_1  = len(_df[_df['growth'] == 1]['cell_lbl'].unique())
                num_class_0 = len(_df[_df['growth'] == 0]['cell_lbl'].unique())          
                num_class_total = num_class_1+num_class_0
                percentage_class_1 = (num_class_1*100)/num_class_total
                percentage_class_1 = format(percentage_class_1, '.2f')
                plot_title = f"{condition_values[0]} - {condition_values[1]} (n = {num_cells} cells, class_1 = {num_class_1} of {num_class_total} cells - {percentage_class_1}%)"  # Set the plot title with both condition values
            elif len(condition_values) == 1:
                _df = filtered_cells_df[filtered_cells_df[selected_condition] == condition_values[0]]
                num_cells = len(_df['cell_lbl'].unique())
                num_class_1  = len(_df[_df['growth'] == 1]['cell_lbl'].unique())
                num_class_0 = len(_df[_df['growth'] == 0]['cell_lbl'].unique())                   
                num_class_total = num_class_1+num_class_0
                percentage_class_1 = (num_class_1*100)/num_class_total
                percentage_class_1 = format(percentage_class_1, '.2f')
                plot_title = f"{condition_values[0]} (n = {num_cells} cells, class_1 = {num_class_1} of {num_class_total} cells - {percentage_class_1}%)"  # Set the plot title with both condition values
            else:
                continue  # if there are no conditions, continue to the next iteration

            _df = _df.copy()
            _df['t'] = _df['t'].astype(int)
            _df.sort_values(by=['cell_lbl', 't'], inplace=True)  # Sort by 'cell_lbl' and 't'

            fig, ax = plt.subplots(figsize=(12, 4))  # New figure for each condition
            ax.set_title(plot_title)
            ax.set_ylabel(selected_parameter)
            ax.set_xlabel('time')
            if yMin is not None and yMax is not None:
                ax.set_ylim(yMin, yMax)


            # normalization = data['normalization']
            normalization = data.get('normalization', 'none')


            if normalization == 't0':
                # Normalize the data to t=0
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    t0_value = group.loc[group['t'].idxmin(), selected_parameter]
                    group[selected_parameter] /= t0_value
                    _df.loc[group.index, selected_parameter] = group[selected_parameter]
                    # if t0_value == 0:
                    #     t0_value = 1e-10  # Substitute a small positive number for t0_value
                    # group[selected_parameter] /= t0_value
                    # _df.loc[group.index, selected_parameter] = group[selected_parameter]
            
            # Normalize custom
            elif normalization == 'custom':
                range_start = int(data.get('range_start', 0))
                range_end = int(data.get('range_end', 4))

                for cell_lbl, group in _df.groupby('cell_lbl'):
                    average_value = group[(group['t'] >= range_start) & (group['t'] <= range_end)][selected_parameter].mean()
                    if average_value != 0:  # Avoid division by zero
                        group[selected_parameter] /= average_value
                        _df.loc[group.index, selected_parameter] = group[selected_parameter]

                # Delta normalization
                # elif normalization == 'delta':
                #     for cell_lbl, group in _df.groupby('cell_lbl'):
                #         group[selected_parameter] = group[selected_parameter] / group[selected_parameter].shift(1)
                #         _df.loc[group.index, selected_parameter] = group[selected_parameter]

            elif normalization == 'delta':
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    group[selected_parameter] = group[selected_parameter].diff()
                    _df.loc[group.index, selected_parameter] = group[selected_parameter]


            # Set the x-axis limit for each plot and colours
            ax.set_xlim(t_min, t_max)

            # Prepare color palette
            growth_color_map = {0: 'blue', 1: 'red'}      

            for lbl, gr in _df.groupby('cell_lbl'):
                if gr['growth'].unique() == 0:
                    # settings for class_0 cells plot
                    col = np.array( (72, 219, 251) )/255 # color blue
                else:
                    # settings for class_1 cells plot
                    col = np.array( (238, 32, 77) )/255 # color red
                ax.plot( gr['t'].values, gr[selected_parameter].values, '-', color = col, alpha=0.1, lw=1 )
  
        
            # population average
            sns.lineplot( data=_df, x='t', y=selected_parameter,
                     hue='growth', palette=growth_color_map, 
                     ax=ax, linewidth=2, estimator=np.median )

            # Display both colors in the legend
            handles, labels = ax.get_legend_handles_labels()
            # handles[0] is the legend title, handles[1] is for 'growth=0', and handles[2] is for 'growth=1'.
            ax.legend(handles=handles, labels=labels)

            # To add the general name above the legend
            ax.legend(title='class')

            # Set legend location
            ax.legend(loc='upper right')
            
            # # To remove legend title
            # handles, labels = ax.get_legend_handles_labels()
            # ax.legend(handles=handles[1:], labels=labels[1:])       
            
            timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
            condition_names = '_'.join(str(condition) for condition in condition_values)
            plot4_path = f"plot_backward_{selected_parameter}_{condition_names}_{current_filename}_{timestamp}.png"
            _df.to_csv(f"computed_data/backward/table_{plot4_path.split('.')[0]}.csv")
            plt.savefig('computed_data/backward/' + plot4_path)

            plot_urls_backward.append(url_for('serve_backward', path=plot4_path))
            print(plot_urls_backward)

    except Exception as e:
        app.logger.error(f'Error generating plot: {e}')
        return jsonify({'message': f'Error generating plot: {e}'}), 500

    response = {
        'message': 'Plots created successfully',
        'plot_urls_backward': plot_urls_backward  # Return multiple plot URLs
    }

    return jsonify(response), 200

@app.route('/download_backward', methods=['GET'])
def download_results_backward():
    try:
        # create a temporary directory
        os.makedirs('temp', exist_ok=True)

        # copy files to temporary directory
        shutil.copytree('computed_data/backward', 'temp/backward')

        # create timestamp
        timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")

        # create zip file
        shutil.make_archive(f'results_backward_{timestamp}', 'zip', 'temp')

        # remove temporary directory
        shutil.rmtree('temp')

        return send_file(f'results_backward_{timestamp}.zip',
                         mimetype='zip',
                         attachment_filename=f'results_backward_{timestamp}.zip',
                         as_attachment=True)
    except FileNotFoundError:
        abort(404)
















# # # # # # # # # # # # # #

if __name__ == '__main__':
    app.run(port=5000)
