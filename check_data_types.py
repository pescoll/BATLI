import pandas as pd

def print_column_data_types(filename):
    df = pd.read_csv(filename)
    print(df.dtypes)

# Replace with your filename
print_column_data_types('/Users/pedro/Documents/GitHub/backward_analysis/cleaned_dataset_EP128REDUCED-W1-TMRM_Measurement_1_Evaluation10_Population_-_Cells.csv')
