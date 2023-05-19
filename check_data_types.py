import pandas as pd

def print_column_data_types(filename):
    df = pd.read_csv(filename)
    print(df.dtypes)

# Replace with your filename
print_column_data_types('/Users/pedroescoll/Documents/GitHub/backward_analysis/cleaned_dataset_EP167_Measurement_1_Evaluation2_Population_-_Infected.csv')
