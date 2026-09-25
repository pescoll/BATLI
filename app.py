from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, send_file, abort, current_app
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from numpy.polynomial.polynomial import Polynomial
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

    print(cells_df.columns)  # print column names before the operation
    cells_df.columns = cells_df.columns.str.lower().str.replace(' ', '_')
    print(cells_df.columns)  # print column names after the operation

    return cells_df

def find_infected_column(df):
    # Return the name of the infected-status column: 'infected' or 'IF' (any capitalization), or None if absent
    for col in df.columns:
        if isinstance(col, str) and col.lower() in ('infected', 'if'):
            return col
    return None

def passes_threshold(dA, th):
    # Positive threshold: pass if the value increases by at least `th`.
    # Negative threshold: pass if the value decreases by at least |th|.
    return dA >= th if th >= 0 else dA <= th

def classification_tags(percentage, threshold, threshold2=None, threshold_b1=None, threshold_b2=None):
    # Short tags describing the classification settings used in plot3.
    # Examples (title tag -> filename tag):
    #   classic 2-class:        'th:15,50%'           -> 'th15_50'
    #   3-class:                'th:15/-14,50%'       -> 'th15_-14_50'
    #   2 parameters:           'th:15&-10,50%'       -> 'th15+-10_50'
    #   2 params + 3 classes:   'th:15&-10/-14&5,50%' -> 'th15+-10_-14+5_50'
    # ('&' joins the two parameter thresholds of one class, '/' separates class 1 from class 2)
    def fmt(v):
        return f"{float(v):g}"
    th_str = fmt(threshold)
    if threshold_b1 is not None:
        th_str += '&' + fmt(threshold_b1)
    if threshold2 is not None:
        part2 = fmt(threshold2)
        if threshold_b2 is not None:
            part2 += '&' + fmt(threshold_b2)
        th_str += '/' + part2
    title_tag = f"th:{th_str},{percentage}%"
    file_tag = 'th' + th_str.replace('&', '+').replace('/', '_').replace('.', 'p') + f"_{percentage}"
    return title_tag, file_tag

def class_summary(_df, include_class_2=False):
    # Per-condition class counts for plot titles, e.g. 'class_1 = 86 of 1215 cells - 7.08%'
    total = _df['cell_lbl'].nunique()
    parts = []
    for cls in ([1, 2] if include_class_2 else [1]):
        n = _df[_df['growth'] == cls]['cell_lbl'].nunique()
        pct = format((n * 100) / total, '.2f') if total else '0.00'
        parts.append(f"class_{cls} = {n} of {total} cells - {pct}%")
    return ', '.join(parts)

@app.route('/')
def index():
    return render_template('index.html')

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

# INSTRUCTIONS
@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

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

        filename = filename.rsplit('.', 1)[0] + '.json'

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

    # # Load the cleaned dataset into a DataFrame

    # Read the file content
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
        file_content = f.read()

    # Replace semicolons with commas
    file_content = file_content.replace(';', ',')

    # Use StringIO to read the file content into a DataFrame
    cells_df = pd.read_csv(io.StringIO(file_content))

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
    conditions_cols = ['bacteria', 'bact', 'compound', 'treatment', 'pretreatment', 'assay', 'assays', 'assay_number', 'moi', 'concentration', 'cell_type'] # list of conditions columns
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
    print(f"Data received: {data}")
    selected_condition = data['condition']
    selected_second_condition = data.get('secondCondition')  # This will be None if not provided
    print(f"Selected second condition (server side): {selected_second_condition}")
    selected_third_condition = data.get('thirdCondition')  # This will be None if not provided
    fixed_third_condition = data.get('fixedThirdCondition')
    if isinstance(fixed_third_condition, str):
        fixed_third_condition = fixed_third_condition.lower() == 'true'
    print(f"Fixed third condition (server side): {fixed_third_condition}")
    fixed_third_condition_value = data.get('fixedThirdConditionValue')
    selected_parameter = data['parameter']
    percentage = int(data['percentage'])
    plot_style = data.get('plotStyle', 'original')  # 'original' (BATLI classic) or 'publication'

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

    # Define the test_length function
    def test_length(group):
        return len(group) >= required_timepoints

    # Filter the dataframe
    filtered_cells_df = cells_df.groupby('cell_lbl').filter(test_length).copy()

    # Output for verification
    print("Total timepoints: ", total_timepoints)
    print("Required timepoints: ", required_timepoints)
    print("Number of unique cell_lbl in original df: ", len(cells_df['cell_lbl'].unique()))
    print("Number of unique cell_lbl in filtered df: ", len(filtered_cells_df['cell_lbl'].unique()))
    
    sub_df = filtered_cells_df[selected_condition].unique()

    float('inf')  # Returns: inf
    float('-inf')  # Returns: -inf

    plot_urls = []

    try:
        if fixed_third_condition:
            if selected_third_condition is None:
                return jsonify({'message': 'Third condition is fixed but no third condition was selected. Please select a third condition or uncheck the fixed third condition option.'}), 400
            # get the type of the first value in the selected_third_condition column
            third_condition_type = type(filtered_cells_df[selected_third_condition].iloc[0])
            third_condition_value = third_condition_type(fixed_third_condition_value)
            filtered_df = filtered_cells_df[filtered_cells_df[selected_third_condition] == third_condition_value]

            if selected_second_condition and selected_second_condition != 'none':
                condition_combinations = filtered_df[[selected_condition, selected_second_condition]].drop_duplicates().values.tolist()
            else:
                condition_combinations = [(value, third_condition_value) for value in filtered_df[selected_condition].unique()]
        else:
            if selected_second_condition and selected_second_condition != 'none' and selected_third_condition and selected_third_condition != 'none':
                condition_combinations = filtered_cells_df[[selected_condition, selected_second_condition, selected_third_condition]].drop_duplicates().values.tolist()
            elif selected_second_condition and selected_second_condition != 'none':
                condition_combinations = filtered_cells_df[[selected_condition, selected_second_condition]].drop_duplicates().values.tolist()
            elif selected_third_condition and selected_third_condition != 'none':
                condition_combinations = [(value, third_condition_value) for value in filtered_cells_df[selected_condition].unique()]
            else:
                condition_combinations = [(value,) for value in filtered_cells_df[selected_condition].unique()]

        print(f"Fixed third condition: {fixed_third_condition}")
        print(f"Fixed third condition value: {fixed_third_condition_value}")
        print(f"Condition combinations: {condition_combinations}")  # print to debug

        # Check if condition_combinations is empty
        if not condition_combinations:
            response = {
                'message': 'No plots can be created with the selected conditions. Please adjust your selection and try again.',
                'plot_urls': []  # Return an empty list as there are no plot URLs
            }
            return jsonify(response), 400  # Use HTTP status code 400 (Bad Request) to indicate a user error

        for condition_values in condition_combinations:
            # Filter out None values from condition_values
            condition_values = [value for value in condition_values if value is not None]

            if not condition_values:
                # If all values were None, skip this iteration
                continue
            
            if fixed_third_condition:
                if selected_second_condition is not None:
                    _df = filtered_cells_df[(filtered_cells_df[selected_condition] == condition_values[0]) & 
                                            (filtered_cells_df[selected_second_condition] == condition_values[1]) & 
                                            (filtered_cells_df[selected_third_condition] == third_condition_value)]
                    num_cells = len(_df['cell_lbl'].unique())
                    plot_title = f"{condition_values[0]} - {condition_values[1]} - {third_condition_value} (n = {num_cells} cells)"  # Set the plot title with all condition values
                else:
                    _df = filtered_cells_df[(filtered_cells_df[selected_condition] == condition_values[0]) & 
                                            (filtered_cells_df[selected_third_condition] == third_condition_value)]
                    num_cells = len(_df['cell_lbl'].unique())
                    plot_title = f"{condition_values[0]} - {third_condition_value} (n = {num_cells} cells)"  # Set the plot title with condition and third_condition_value
            elif len(condition_values) == 3:
                _df = filtered_cells_df[(filtered_cells_df[selected_condition] == condition_values[0]) & 
                                        (filtered_cells_df[selected_second_condition] == condition_values[1]) & 
                                        (filtered_cells_df[selected_third_condition] == condition_values[2])]
                num_cells = len(_df['cell_lbl'].unique())
                plot_title = f"{condition_values[0]} - {condition_values[1]} - {condition_values[2]} (n = {num_cells} cells)"  # Set the plot title with all condition values
            elif len(condition_values) == 2:
                _df = filtered_cells_df[(filtered_cells_df[selected_condition] == condition_values[0]) & 
                                        (filtered_cells_df[selected_second_condition] == condition_values[1])]
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

            if plot_style == 'publication':
                fig, ax = plt.subplots(figsize=(9, 9))  # Publication mode: square figure
                ax.set_title(plot_title)
                ax.set_ylabel(selected_parameter, fontsize=30)
                ax.set_xlabel('time', fontsize=30)
            else:
                fig, ax = plt.subplots(figsize=(12, 4))  # Original BATLI figure
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
            elif normalization == 'delta':
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    group[selected_parameter] = group[selected_parameter].diff()
                    _df.loc[group.index, selected_parameter] = group[selected_parameter]

            # Set the x-axis limit for each plot
            ax.set_xlim(t_min, t_max)
      
            if normalization == 'curve fitting':
                # # Get the number of unique cells
                # num_cells = len(_df['cell_lbl'].unique())
        
                # # Create a colormap with enough colors
                # colormap = plt.cm.get_cmap('gist_ncar', num_cells)
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    # Subset df to get data of this particular object
                    sub_df = _df[_df['cell_lbl'] == cell_lbl]      

                # for i, (cell_lbl, group) in enumerate(_df.groupby('cell_lbl')):
                #     # Subset df to get data of this particular object
                    sub_df = _df[_df['cell_lbl'] == cell_lbl]

                    # Extract the x and y data for polynomial fitting
                    x = sub_df['t'].values
                    y = sub_df[selected_parameter].values

                    # Perform polynomial regression with degree 5
                    coef = np.polyfit(x, y, 5)
                    poly1d_fn = np.poly1d(coef)

                    # Create a smooth line by predicting y for a range of x values
                    x_line = np.linspace(x.min(), x.max(), 500)
                    y_line = poly1d_fn(x_line)

                    # Plot the fitted curve
                    ax.plot(x_line, y_line, alpha=0.08)
            else:
                for k, v in _df.groupby('cell_lbl').groups.items():
                    single_cell_df = _df.loc[v]  # Subset of data that has only one cell
                    if plot_style == 'publication':
                        ax.plot(single_cell_df['t'], single_cell_df[selected_parameter], alpha=0.2, lw=1)  # publication: more visible traces
                    else:
                        ax.plot(single_cell_df['t'], single_cell_df[selected_parameter], alpha=0.08)  # original BATLI transparency
            
            timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
            condition_names = '_'.join(str(condition) for condition in condition_values)
            plot2_path = f"plot_single_cells_{condition_names}_{current_filename}_{timestamp}.png"
            _df.to_csv(f"computed_data/tables/table_{plot2_path.split('.')[0]}.csv")
            plt.savefig('computed_data/plots/' + plot2_path)

            plot_urls.append(url_for('serve_plots', path=plot2_path))

    except Exception as e:
        current_app.logger.error(f'Error generating plot: {str(e)}')
        raise
        # app.logger.error(f'Error generating plot: {str(e)}')
        # return jsonify({'message': f'Error generating plot: {str(e)}'}), 500

    response = {
        'message': 'Plots created successfully',
        'plot_urls': plot_urls  # Return multiple plot URLs
    }

    return jsonify(response), 200

@app.route('/get_third_condition_values', methods=['POST'])
def get_third_condition_values():
    if current_filename is None:
        return jsonify({'message': 'No file loaded'}), 400

    condition = request.get_json().get('condition')

    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], current_filename))
    unique_values = cells_df[condition].unique().tolist()
    return jsonify(unique_values=unique_values)

@app.route('/download', methods=['GET'])
def download_results():
    try:
        # Create necessary directories
        os.makedirs('temp', exist_ok=True)
        os.makedirs('user_data', exist_ok=True)

        # Copy files to the temporary directory
        shutil.copytree('computed_data/plots', 'temp/plots')
        shutil.copytree('computed_data/tables', 'temp/tables')

        # Create a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")

        # Define the path to save the zip file in /user_data
        zip_filename = f'results_{timestamp}.zip'
        zip_filepath = os.path.join('user_data', zip_filename)

        # Create the zip file in the user_data directory
        shutil.make_archive(base_name=zip_filepath[:-4], format='zip', root_dir='temp')

        # Remove the temporary directory
        shutil.rmtree('temp')

        # Send the file to the client from the user_data directory
        return send_file(zip_filepath,
                         mimetype='application/zip',
                         download_name=zip_filename,
                         as_attachment=True)
    except FileNotFoundError:
        abort(404)



# BACKTRACKING ANALYSIS

@app.route('/backward')
def backward():
    return render_template('backward.html')

@app.route('/get_parameter_names_backward_1', methods=['GET'])
def get_parameter_names_backward_1():
    if current_filename is None:
        return jsonify({'message': 'No file loaded'}), 400
    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], current_filename))
    conditions_cols = ['bacteria', 'bact', 'compound', 'treatment', 'pretreatment', 'assay', 'assays', 'assay_number', 'moi', 'concentration', 'cell_type'] # list of conditions columns
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
    selected_third_condition = data.get('thirdCondition')  # This will be None if not provided
    fixed_third_condition = data.get('fixedThirdCondition')
    if isinstance(fixed_third_condition, str):
        fixed_third_condition = fixed_third_condition.lower() == 'true'
    fixed_third_condition = bool(fixed_third_condition)
    fixed_third_condition_value = data.get('fixedThirdConditionValue')
    selected_parameter = data['parameter']
    percentage = int(data['percentage'])
    threshold = float(data['threshold'])

    # Optional second threshold on the same parameter -> defines class 2 (3-class mode)
    threshold2 = data.get('threshold2')
    threshold2 = float(threshold2) if threshold2 is not None else None

    # Optional second classification parameter with its own threshold(s).
    # A class then requires BOTH parameter conditions to pass (AND logic).
    param2 = data.get('secondClassParameter')
    if param2 in (None, '', 'none'):
        param2 = None
    threshold_b1 = data.get('thresholdB1')
    threshold_b1 = float(threshold_b1) if threshold_b1 is not None else None
    threshold_b2 = data.get('thresholdB2')
    threshold_b2 = float(threshold_b2) if threshold_b2 is not None else None
    if param2 is not None and threshold_b1 is None:
        return jsonify({'message': 'A second classification parameter was selected but its threshold is missing. Please provide it or set the parameter to None.'}), 400
    if param2 is None:
        threshold_b1 = None
        threshold_b2 = None
    if threshold2 is None:
        threshold_b2 = None

    cells_df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], current_filename))

    if param2 is not None and param2 not in cells_df.columns:
        return jsonify({'message': f'Second classification parameter "{param2}" not found in the dataset.'}), 400

    # Analyzing only infected cells in Infected wells (column can be named 'infected' or 'IF')
    if 'bacteria' in cells_df.columns:
        infected_col = find_infected_column(cells_df)
        if infected_col is not None:
            print(f'Analyzing infection! (infected-status column: {infected_col})')
            cells_df = cells_df[~((cells_df['bacteria'] != 'NI') & (cells_df[infected_col] == 0))]

    # If the third condition is fixed, restrict the whole analysis (including the
    # classification) to the cells matching the fixed value
    third_condition_value = None
    if fixed_third_condition:
        if not selected_third_condition or selected_third_condition == 'none':
            return jsonify({'message': 'Third condition is fixed but no third condition was selected. Please select a third condition or uncheck the fixed third condition option.'}), 400
        if selected_third_condition not in cells_df.columns:
            return jsonify({'message': f'Third condition "{selected_third_condition}" not found in the dataset.'}), 400
        third_condition_type = type(cells_df[selected_third_condition].iloc[0])
        third_condition_value = third_condition_type(fixed_third_condition_value)
        cells_df = cells_df[cells_df[selected_third_condition] == third_condition_value]
        if cells_df.empty:
            return jsonify({'message': f'No cells found for {selected_third_condition} = {fixed_third_condition_value}. Please adjust your selection.'}), 400

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

    # Filter the DataFrame to only include cell_lbl's that pass the test_length function
    # Use .filter() instead of .transform() for better reliability
    filtered_cells_df = cells_df.groupby('cell_lbl').filter(test_length).copy()

    print("Number of unique cell_lbl in original df: ", len(cells_df['cell_lbl'].unique()))
    print("Number of unique cell_lbl in filtered df: ", len(filtered_cells_df['cell_lbl'].unique()))
    
    sub_df = filtered_cells_df[selected_condition].unique()

    float('inf')  # Returns: inf
    float('-inf')  # Returns: -inf

    plot_urls_backward = []

    # lists that hold cells ids:
    class_2 = []
    class_1 = []
    class_0 = []

    filtered_cells_df.sort_values(by=['cell_lbl', 't'], inplace=True)  # Sort by 'cell_lbl' and 't'

    # number of points to average (N), adjust if necessary, will be used to determine growth
    Np = 2

    # go over each cell:
    for lbl, gr in filtered_cells_df.groupby(['cell_lbl']):
        lbl = lbl[0] if isinstance (lbl, tuple) else lbl
        # times = gr['t'].values
        growth = gr[selected_parameter].values 
        # calculate Area change:
        # array[-N:] -> returns last N elements
        # array[0:N] -> returns first N elements
        dA = float(growth[-Np:].mean() - growth[0:Np].mean())
        # Change of the optional second classification parameter
        dA2 = None
        if param2 is not None:
            growth2 = gr[param2].values
            dA2 = float(growth2[-Np:].mean() - growth2[0:Np].mean())

        # Thresholds work in both directions (see passes_threshold):
        # positive = increase of at least th, negative = decrease of at least |th|.
        # Class 2 (if enabled) is evaluated first, then class 1, otherwise class 0.
        # With a second parameter, a class requires BOTH parameter conditions (AND).
        if threshold2 is not None and passes_threshold(dA, threshold2) and \
           (threshold_b2 is None or passes_threshold(dA2, threshold_b2)):
            class_2.append( lbl )
        elif passes_threshold(dA, threshold) and \
             (threshold_b1 is None or passes_threshold(dA2, threshold_b1)):
            class_1.append( lbl )
            print(lbl, growth[-Np:].mean(), growth[0:Np].mean(), dA)
        else:
            class_0.append( lbl )

    # add column growth: 0 by default, 1 for class_1 cells, 2 for class_2 cells
    filtered_cells_df['growth'] = 0
    filtered_cells_df.loc[filtered_cells_df['cell_lbl'].isin( class_1 ), 'growth'] = 1
    filtered_cells_df.loc[filtered_cells_df['cell_lbl'].isin( class_2 ), 'growth'] = 2
    filtered_cells_df.to_csv(f"computed_data/backward/table_single_cells_filtered.csv")

    # Save the classification settings so plot4 can tag its graphs with them
    with open('computed_data/backward/classification_info.json', 'w') as f:
        json.dump({'threshold': threshold, 'percentage': percentage,
                   'threshold2': threshold2, 'parameter': selected_parameter,
                   'parameter2': param2, 'threshold_b1': threshold_b1,
                   'threshold_b2': threshold_b2}, f)

    # Short tags describing the classification settings, for titles and filenames
    title_tag, file_tag = classification_tags(percentage, threshold, threshold2, threshold_b1, threshold_b2)

    total_cells = len(class_0) + len(class_1) + len(class_2)
    print( 'Class_1 / class_2 / total cells: %d / %d / %d'%(len(class_1), len(class_2), total_cells) )
    print(class_1)
    try:
        # Columns whose value combinations define one plot each. The third condition
        # joins the combinations only when it is not fixed (fixed = already filtered).
        combo_cols = [selected_condition]
        if selected_second_condition and selected_second_condition != 'none':
            combo_cols.append(selected_second_condition)
        if (not fixed_third_condition) and selected_third_condition and selected_third_condition != 'none':
            combo_cols.append(selected_third_condition)
        condition_combinations = filtered_cells_df[combo_cols].drop_duplicates().values.tolist()

        print(f"Condition combinations: {condition_combinations}")  # print to debug

        for condition_values in condition_combinations:
            mask = pd.Series(True, index=filtered_cells_df.index)
            for col, val in zip(combo_cols, condition_values):
                mask &= (filtered_cells_df[col] == val)
            _df = filtered_cells_df[mask]
            if _df.empty:
                continue
            num_cells = len(_df['cell_lbl'].unique())
            title_values = [str(v) for v in condition_values]
            if fixed_third_condition:
                title_values.append(str(third_condition_value))
            plot_title = f"{' - '.join(title_values)} (n = {num_cells} cells, {class_summary(_df, threshold2 is not None)}) {title_tag}"

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


            elif normalization == 'delta':
                for cell_lbl, group in _df.groupby('cell_lbl'):
                    group[selected_parameter] = group[selected_parameter].diff()
                    _df.loc[group.index, selected_parameter] = group[selected_parameter]

            # Set the x-axis limit for each plot
            ax.set_xlim(t_min, t_max)
   
            # select a subset of data for each class
            _df_class_2 = _df[_df['growth']==2]
            _df_class_1 = _df[_df['growth']==1]
            _df_class_0 = _df[_df['growth']==0]

            for lbl, gr in _df_class_0.groupby('cell_lbl'):
                    ax.plot( gr['t'], gr[selected_parameter], 'b-', alpha=0.05)

            for lbl, gr in _df_class_1.groupby('cell_lbl'):
                    ax.plot( gr['t'], gr[selected_parameter], 'r-', alpha=0.5 )

            for lbl, gr in _df_class_2.groupby('cell_lbl'):
                    ax.plot( gr['t'], gr[selected_parameter], 'g-', alpha=0.5 )
            
            timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
            condition_names = '_'.join(title_values)
            plot3_path = f"plot_backward_classes_{condition_names}_{file_tag}_{current_filename}_{timestamp}.png"
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
    conditions_cols2 = ['bacteria', 'bact', 'compound', 'treatment', 'pretreatment', 'assay', 'assays', 'assay_number', 'moi', 'concentration', 'cell_type'] # list of conditions columns
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
    selected_third_condition = data.get('thirdCondition')  # This will be None if not provided
    fixed_third_condition = data.get('fixedThirdCondition')
    if isinstance(fixed_third_condition, str):
        fixed_third_condition = fixed_third_condition.lower() == 'true'
    fixed_third_condition = bool(fixed_third_condition)
    fixed_third_condition_value = data.get('fixedThirdConditionValue')
    selected_parameter = data['parameter']
    percentage = int(data['percentage'])
    plot_style = data.get('plotStyle', 'original')  # 'original' (BATLI classic) or 'publication'

    # Read the dataframe
    filename = "table_single_cells_filtered.csv"
    directory = "computed_data/backward"
    path = os.path.join(directory, filename)

    cells_df = pd.read_csv(path)

    # Load the classification settings saved by plot3 (thresholds and % track length)
    # to tag titles and filenames of the backtracking graphs
    title_tag = ''
    file_tag = ''
    class_info = None
    class_info_path = os.path.join(directory, 'classification_info.json')
    if os.path.exists(class_info_path):
        with open(class_info_path, 'r') as f:
            class_info = json.load(f)
        title_tag, file_tag = classification_tags(class_info['percentage'],
                                                  class_info['threshold'],
                                                  class_info.get('threshold2'),
                                                  class_info.get('threshold_b1'),
                                                  class_info.get('threshold_b2'))

    # Whether the classification used 3 classes (0, 1, 2)
    include_class_2 = bool((class_info is not None and class_info.get('threshold2') is not None)
                           or (cells_df['growth'] == 2).any())

    # If 'bacteria' column exists, analyze only infected cells in infected wells
    # (infected-status column can be named 'infected' or 'IF')
    if 'bacteria' in cells_df.columns:
        infected_col = find_infected_column(cells_df)
        if infected_col is not None:
            print(f'Analyzing infection! (infected-status column: {infected_col})')
            cells_df = cells_df[~((cells_df['bacteria'] != 'NI') & (cells_df[infected_col] == 0))]

    # If the third condition is fixed, restrict the plots to the cells matching the fixed value
    third_condition_value = None
    if fixed_third_condition:
        if not selected_third_condition or selected_third_condition == 'none':
            return jsonify({'message': 'Third condition is fixed but no third condition was selected. Please select a third condition or uncheck the fixed third condition option.'}), 400
        if selected_third_condition not in cells_df.columns:
            return jsonify({'message': f'Third condition "{selected_third_condition}" not found in the dataset.'}), 400
        third_condition_type = type(cells_df[selected_third_condition].iloc[0])
        third_condition_value = third_condition_type(fixed_third_condition_value)
        cells_df = cells_df[cells_df[selected_third_condition] == third_condition_value]
        if cells_df.empty:
            return jsonify({'message': f'No cells found for {selected_third_condition} = {fixed_third_condition_value}. Please adjust your selection.'}), 400

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

    # Filter the DataFrame to only include cell_lbl's that pass the test_length function
    # Use .filter() instead of .transform() for better reliability
    filtered_cells_df = cells_df.groupby('cell_lbl').filter(test_length).copy()

    print("Number of unique cell_lbl in original df: ", len(cells_df['cell_lbl'].unique()))
    print("Number of unique cell_lbl in filtered df: ", len(filtered_cells_df['cell_lbl'].unique()))
    
    sub_df = filtered_cells_df[selected_condition].unique()

    float('inf')  # Returns: inf
    float('-inf')  # Returns: -inf

    plot_urls_backward = []

    try:
        # Columns whose value combinations define one plot each. The third condition
        # joins the combinations only when it is not fixed (fixed = already filtered).
        combo_cols = [selected_condition]
        if selected_second_condition and selected_second_condition != 'none':
            combo_cols.append(selected_second_condition)
        if (not fixed_third_condition) and selected_third_condition and selected_third_condition != 'none':
            combo_cols.append(selected_third_condition)
        condition_combinations = filtered_cells_df[combo_cols].drop_duplicates().values.tolist()

        print(f"Condition combinations: {condition_combinations}")  # print to debug

        for condition_values in condition_combinations:
            mask = pd.Series(True, index=filtered_cells_df.index)
            for col, val in zip(combo_cols, condition_values):
                mask &= (filtered_cells_df[col] == val)
            _df = filtered_cells_df[mask]
            if _df.empty:
                continue
            num_cells = len(_df['cell_lbl'].unique())
            title_values = [str(v) for v in condition_values]
            if fixed_third_condition:
                title_values.append(str(third_condition_value))
            plot_title = f"{' - '.join(title_values)} (n = {num_cells} cells, {class_summary(_df, include_class_2)}) {title_tag}"

            _df = _df.copy()
            _df['t'] = _df['t'].astype(int)
            _df.sort_values(by=['cell_lbl', 't'], inplace=True)  # Sort by 'cell_lbl' and 't'

            if plot_style == 'publication':
                fig, ax = plt.subplots(figsize=(9, 9))  # Publication mode: square figure
                ax.set_title(plot_title)
                ax.set_ylabel(selected_parameter, fontsize=30)
                ax.set_xlabel('time', fontsize=30)
                ax.tick_params(axis='both', which='major', labelsize=30)  # Change font size for tick labels
            else:
                fig, ax = plt.subplots(figsize=(12, 4))  # Original BATLI figure
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

            if plot_style == 'publication':
                # Publication mode: darker colors, thicker/more visible traces, no median overlay or legend
                pub_colors = {0: np.array( (51, 153, 255) )/255,   # class_0 blue
                              1: np.array( (147, 19, 4) )/255,     # class_1 dark red
                              2: np.array( (34, 139, 34) )/255}    # class_2 dark green
                for lbl, gr in _df.groupby('cell_lbl'):
                    col = pub_colors.get(int(gr['growth'].iloc[0]), pub_colors[0])
                    ax.plot( gr['t'].values, gr[selected_parameter].values, '-', color = col, alpha=0.2, lw=2 )
            else:
                # Original BATLI graphs
                orig_colors = {0: np.array( (72, 219, 251) )/255,  # class_0 blue
                               1: np.array( (238, 32, 77) )/255,   # class_1 red
                               2: np.array( (50, 205, 50) )/255}   # class_2 green
                for lbl, gr in _df.groupby('cell_lbl'):
                    col = orig_colors.get(int(gr['growth'].iloc[0]), orig_colors[0])
                    ax.plot( gr['t'].values, gr[selected_parameter].values, '-', color = col, alpha=0.1, lw=1 )

                # population average (palette restricted to the classes present in this condition)
                present_classes = sorted(_df['growth'].unique())
                growth_color_map = {k: v for k, v in {0: 'blue', 1: 'red', 2: 'green'}.items() if k in present_classes}
                sns.lineplot( data=_df, x='t', y=selected_parameter,
                         hue='growth', palette=growth_color_map,
                         ax=ax, linewidth=2, estimator=np.median )

                # Set legend location
                ax.legend(loc='upper right')

            timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
            condition_names = '_'.join(title_values)
            file_tag_part = f"{file_tag}_" if file_tag else ""
            plot4_path = f"plot_backward_{selected_parameter}_{condition_names}_{file_tag_part}{current_filename}_{timestamp}.png"
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
        # Create a temporary directory
        os.makedirs('temp', exist_ok=True)

        # Copy files to the temporary directory
        shutil.copytree('computed_data/backward', 'temp/backward')

        # Create a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")

        # Define the path to save the zip file in /user_data
        zip_filename = f'results_backtracking_{timestamp}.zip'
        zip_filepath = os.path.join('user_data', zip_filename)

        # Create the zip file in the user_data directory
        shutil.make_archive(base_name=zip_filepath[:-4], format='zip', root_dir='temp')

        # Remove the temporary directory
        shutil.rmtree('temp')

        # Send the file to the client from the user_data directory
        return send_file(zip_filepath,
                         mimetype='application/zip',
                         download_name=zip_filename,
                         as_attachment=True)
    except FileNotFoundError:
        abort(404)


# # # # # # # # # # # # # #

if __name__ == '__main__':
    app.run(port=5001)
