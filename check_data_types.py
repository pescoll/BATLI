import pandas as pd

def print_column_data_types(filename):
    df = pd.read_csv(filename)
    print(df.dtypes)

# Replace with your filename
print_column_data_types('/Users/pedro/Documents/GitHub/backward_analysis/user_data/cleaned_dataset_EP211_Measurement_1_Evaluation1_Population_-_Nuclei.csv')
