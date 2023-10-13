
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ks_2samp
from scipy.stats import mannwhitneyu
from statsmodels.stats.proportion import proportions_ztest
import datetime

# List of dataset paths WT
dataset_paths = [
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_8_cleaned_dataset_MD_06_Measurement_1_Evaluation4_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_NI_7_cleaned_dataset_MD_07_Measurement_1_Evaluation1_Population_-_tracked_cells.csv',
    '',
    '',
    ''
]

# # List of dataset paths dotA
# dataset_paths = [
#     './calculate_vacuoles_scripts/datasets/dataset_1_dotA.csv',
#     '',
#     '',
#     '',
#     ''
# ]


# Doubling factor, adjust this value as per your requirements
double_factor = 2.5 

# # Function to calculate duplication not including current row
# def calculate_duplication(group):
#     # Shift the series down by one and then calculate expanding mean
#     shifted_series = group['bacterial_area_[um²]-_sum_per_cell_'].shift(1)
#     group['duplication'] = (group['bacterial_area_[um²]-_sum_per_cell_'] >= double_factor * shifted_series.expanding().mean()).astype(int)
#     return group

def calculate_duplication(group):
    # Initialize 'duplication' column with NaN values
    group['duplication'] = np.nan
    
    # List to hold the calculated means
    means = []
    
    # List to hold the non-zero values
    non_zero_values = []
    
    # Calculate means for all consecutive non-zero values
    for idx, row in group.iterrows():
        value = row['bacterial_area_[um²]-_sum_per_cell_']
        if value != 0.00:
            non_zero_values.append(value)
            if len(non_zero_values) >= 3:
                means.append(np.mean(non_zero_values))
                
    # Compare each row with all the calculated means
    for idx, row in group.iterrows():
        value = row['bacterial_area_[um²]-_sum_per_cell_']
        for mean_idx, mean in enumerate(means):
            if value >= double_factor * mean:
                group.at[idx, 'duplication'] = 1  # Tag as duplication
                break  # Exit the loop if condition is met
                
    return group


for dataset_path in dataset_paths:
    if not dataset_path.strip():  # Skip if path is empty
        continue

    # Load the data
    df = pd.read_csv(dataset_path)

    # Filter the DataFrame
    df_filtered = df[df['growth'] == 0]

    # Sorting by cell_lbl and t, to ensure the time series for each cell is in correct order
    df_sorted = df_filtered.sort_values(['cell_lbl', 't'])

    # Extract dataset name for file naming
    dataset_name = dataset_path.split('/')[-1].replace('.csv', '')
    
    # Applying the function to each group
    df_final = df_sorted.groupby('cell_lbl').apply(calculate_duplication)

    # Save file
    timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
    results_path = f"./calculate_vacuoles_scripts/results/results_{dataset_name}_{timestamp}.csv"
    df_final.to_csv(results_path, index=False)

    # Print the number of unique cell_IDs
    print("Number of unique cell_IDs:", df_final['cell_lbl'].nunique())

    # Count total unique cells at each time point
    total_cells = df_final.groupby('t')['cell_lbl'].nunique()

    # Filter the cells that have duplication=1
    df_duplication = df_final[df_final['duplication'] == 1]

    # Count unique cells with duplication=1 at each time point
    duplication_cells = df_duplication.groupby('t')['cell_lbl'].nunique()

    # Calculate the percentage
    percentage = (duplication_cells / total_cells) * 100

    # Reset the index to prepare data for plotting
    percentage_df = percentage.reset_index().rename(columns={'cell_lbl': 'percentage'})

    # Create the bar plot
    plt.figure(figsize=(10, 6))
    sns.barplot(x='t', y='percentage', data=percentage_df)
    plt.title('% of cells which duplicated bacterial area with respect to all previous time points')
    plt.xlabel('Time point')
    plt.ylabel('Percentage (%)')

    # Save the plot as PNG
    plot_path = f"./calculate_vacuoles_scripts/results/bar_graph_{dataset_name}_{timestamp}.png"
    plt.savefig(plot_path)


    # Convert the 'percentage' column back to list for easier calculation
    percentage_list = percentage.tolist()

    # Create a DataFrame from the list
    final_percentage_df = pd.DataFrame({
        'time_point': range(len(percentage_list)),
        'percentage': percentage_list
    })

    # Exporting results: Adjust filenames to be dataset-specific
    percentage_results_path = f"./calculate_vacuoles_scripts/results/percentages_for_{dataset_name}_{timestamp}.csv"
    final_percentage_df.to_csv(percentage_results_path, index=False)

print('FINISHED')
