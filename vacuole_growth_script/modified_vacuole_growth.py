
import pandas as pd
import datetime

# Datasets:
# dataset_1 = MD_18 - vacuole_growth_script/table_plot_backward_bacteria_area_[um²]-_sum_per_cell__WT_5_cleaned_dataset_MD_18_Measurement_2_Evaluation4_Population_-_Tracked_Cells copy.csv
# dataset_2 = MD_30 - vacuole_growth_script/table_plot_backward_legio_area_[um²]-_sum_per_cell__WT_cleaned_dataset_MD_30_Measurement_1_Evaluation2_Population_-_Tracked_Cells copy.csv
# dataset_3 = EP149 - vacuole_growth_script/table_plot_backward_classes_Lpp_WT_cleaned_dataset_EP149_Measurement_1_Evaluation5_Population_-_Tracked_Nuclei copy.csv
# dataset_4 = MD_28 - /vacuole_growth_script/table_plot_backward_classes_WT_cleaned_dataset_MD_28_Measurement_1_Evaluation1_Population_-_Tracked_Cells.csv

# Dataset Paths
dataset_1_path = './vacuole_growth_script/dataset_1.csv'
dataset_2_path = './vacuole_growth_script/dataset_2.csv'
dataset_3_path = './vacuole_growth_script/dataset_3.csv'
dataset_4_path = './vacuole_growth_script/dataset_4.csv'
dataset_1_dotA_path = './vacuole_growth_script/dataset_1_dotA.csv'

# Paths and dataset from the original script
dataset_2_path = './vacuole_growth_script/dataset_2.csv'
dataset = f'dataset_2'

# Load the data
df = pd.read_csv(dataset_2_path)

# Filter the DataFrame
df_filtered = df[df['growth'] == 0]

# Sorting by cell_lbl and t, to ensure the time series for each cell is in correct order
df_sorted = df_filtered.sort_values(['cell_lbl', 't'])

# Doubling factor, adjust this value as per your requirements
double_factor = 2 

# New function to determine significant growth
def calculate_significant_growth(group):
    significant_growth = []
    
    # Iterate through each row in the group
    for idx, current_row in group.iterrows():
        current_area = current_row['bacteria_area']
        
        # Compare with all previous timepoints
        previous_areas = group[group['t'] < current_row['t']]['bacteria_area']
        next_areas = group[group['t'] > current_row['t']]['bacteria_area']
        
        # Check if current_area is significantly larger than all previous areas and smaller than all next areas
        if all(current_area > prev for prev in previous_areas) and all(current_area < nxt for nxt in next_areas):
            significant_growth.append(1)
        else:
            significant_growth.append(0)
    
    group['significant_growth'] = significant_growth
    return group

# Applying the function to each group
df_final = df_sorted.groupby('cell_lbl').apply(calculate_significant_growth)

# Save file
timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
results_path = f"./vacuole_growth_script/results_{dataset}_{timestamp}.csv"
df_final.to_csv(results_path, index=False)


# Calculate the percentage of cells with significant growth for each time point
percentage_df = df_final.groupby('t')['significant_growth'].mean() * 100
percentage_df = percentage_df.reset_index()
percentage_df.columns = ['Time Point', 'Percentage of Cells with Significant Growth']

# Save the percentage results to a new CSV file
percentage_results_path = f"./vacuole_growth_script/results_percentage_{dataset}_{timestamp}.csv"
percentage_df.to_csv(percentage_results_path, index=False)