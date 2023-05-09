from flask import Flask, render_template, request, jsonify
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import os
import json
import pandas as pd
from flask import Flask, request, send_from_directory

app = Flask(__name__)

def clean_dataframe(df, database_info):
    population = database_info["Population"]
    prefix = "Tracked " + population.split(" - ")[1] + " - "
    
    df.columns = [c.replace(prefix, '').replace(' [µm]', '_um').replace('µm', 'um') if isinstance(c, str) else c for c in df.columns]
    
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load_dataset', methods=['POST'])
def load_dataset():
    print("load_dataset() called")
    if 'file' not in request.files:
        return 'No file provided', 400

    file = request.files['file']
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
    df = clean_dataframe(df, database_info)

    # Generate the cleaned dataset file name
    cleaned_dataset_name = f"cleaned_dataset_{database_info['Plate Name']}_{database_info['Measurement']}_{database_info['Evaluation']}_{database_info['Population']}.csv"

    # Save the cleaned dataset as a CSV file
    print("Saving cleaned dataset")
    df.to_csv(cleaned_dataset_name, index=False)

    return 'Dataset successfully loaded and cleaned', 200


if __name__ == '__main__':
    app.run(debug=True)
