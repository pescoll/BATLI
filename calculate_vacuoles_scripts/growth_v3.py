import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colorbar import ColorbarBase
import numpy as np
from scipy.stats import ks_2samp
from scipy.stats import mannwhitneyu
from statsmodels.stats.proportion import proportions_ztest
import datetime
import os
import glob


dataset_dict = {
    'wt' : ( # wt datasets
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_1_cleaned_dataset_MD_28_Measurement_1_Evaluation3_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_Lpp_WT_cleaned_dataset_EP149_Measurement_1_Evaluation5_Population_-_Tracked_Nuclei.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_7_cleaned_dataset_MD_07_Measurement_1_Evaluation1_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_8_cleaned_dataset_MD_06_Measurement_1_Evaluation4_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_8_cleaned_dataset_MD_09_Measurement_1_Evaluation5_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_cleaned_dataset_MD_29_Measurement_1_Evaluation2_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_1_cleaned_dataset_MD_30_Measurement_1_Evaluation2_Population_-_Tracked_Cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_8_cleaned_dataset_MD_13_Measurement_1_Evaluation3_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_6_cleaned_dataset_MD_16_Measurement_1_Evaluation10_Population_-_Tracked_Cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_1_cleaned_dataset_MD_17_Measurement_1_Evaluation3_Population_-_Tracked_Cells.csv'
    ),
    'dotA' : ( # dotA datasets
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_dotA_8_cleaned_dataset_MD_09_Measurement_1_Evaluation5_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_dotA_1_cleaned_dataset_MD_28_Measurement_1_Evaluation3_Population_-_tracked_cells.csv',
    #'./calculate_vacuoles_scripts/datasets/table_plot_backward_classes_dotA_5_cleaned_dataset_MD_18_Measurement_2_Evaluation4_Population_-_Tracked_Cells.csv',
    #'./calculate_vacuoles_scripts/datasets/table_plot_backward_classes_dotA_cleaned_dataset_MD_29_Measurement_1_Evaluation2_Population_-_tracked_cells.csv',
    #'./calculate_vacuoles_scripts/datasets/table_plot_backward_classes_Lpp_dotA_cleaned_dataset_EP149_Measurement_1_Evaluation5_Population_-_Tracked_Nuclei.csv',
    #'./calculate_vacuoles_scripts/datasets/table_plot_backward_classes_dotA_1_cleaned_dataset_MD_30_Measurement_1_Evaluation2_Population_-_Tracked_Cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_dotA_6_cleaned_dataset_MD_16_Measurement_1_Evaluation10_Population_-_Tracked_Cells.csv',
    #'./calculate_vacuoles_scripts/datasets/table_plot_backward_classes_dotA_8_cleaned_dataset_MD_13_Measurement_1_Evaluation3_Population_-_tracked_cells.csv',
    #'./calculate_vacuoles_scripts/datasets/table_plot_backward_classes_dotA_1_cleaned_dataset_MD_17_Measurement_1_Evaluation3_Population_-_Tracked_Cells.csv'
    )}


# Doubling factor, adjust this value as per your requirements
double_factor = 2.5

def delete_all_files_in_directory(directory_path):
    # List all files in the directory
    files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]

    # Delete each file
    for f in files:
        os.remove(os.path.join(directory_path, f))

# Call the function to delete all files in the directory
# Comment out to store data of multiple runs
delete_all_files_in_directory('./calculate_vacuoles_scripts/results_v3')

def calculate_duplication(df):
    # Initialize 'duplication' column with NaN values for the whole DataFrame
    df['duplication'] = np.nan
    
    # Function to apply to each group
    def calculate_group_duplication(group):
        # List to hold the calculated means of previous rows
        previous_means = []
        
        # List to hold the non-zero values of previous rows
        previous_non_zero_values = []
        
        # Iterate through each row in the group
        for idx, row in group.iterrows():
            value = row['bacterial_area_[um²]-_sum_per_cell_']
            
            # Compare the current value with the means of previous rows
            for mean in previous_means:
                if value >= double_factor * mean:
                    group.at[idx, 'duplication'] = 1  # Tag as duplication
                    break  # Exit the loop if condition is met
            
            # Update the list of non-zero values and means based on the current row
            if value != 0.00:
                previous_non_zero_values.append(value)
                if len(previous_non_zero_values) >= 2:
                    mean_of_previous = np.mean(previous_non_zero_values[-5:])  # Last 4 values
                    previous_means.append(mean_of_previous)
        
        return group
    
    # Group the DataFrame by 'cell_lbl' and apply the function to each group
    df = df.groupby('cell_lbl').apply(calculate_group_duplication)
    
    return df


for group, paths in dataset_dict.items():
    print(f"Processing datasets for {group} ...")
    
    # Loop through each dataset path in the group
    for path in paths:
        print(f"Processing dataset at path: {path}")
        if not path.strip():  # Skip if path is empty
            continue

        # Load the data
        df = pd.read_csv(path)

        # Filter the DataFrame
        df_filtered = df[df['growth'] == 0]

        # Sorting by cell_lbl and t, to ensure the time series for each cell is in correct order
        df_sorted = df_filtered.sort_values(['cell_lbl', 't'])

        # Extract dataset name for file naming
        dataset_name = path.split('/')[-1].replace('.csv', '')
    
        # Applying the function to each group
        df_final = df_sorted.groupby('cell_lbl').apply(calculate_duplication)

        # Save file
        timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
        results_path = f"./calculate_vacuoles_scripts/results_v3/results_{dataset_name}_{timestamp}.csv"
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
        plt.title(f'% of cells which duplicated bacterial area with respect to the mean of all previous time points\n{dataset_name}')
        plt.subplots_adjust(top=0.85)
        plt.xlabel('Time point')
        plt.ylabel('Percentage (%)')
        plt.ylim(0, 30)

        # Save the plot as PNG
        plot_path = f"./calculate_vacuoles_scripts/results_v3/bar_graph_{dataset_name}_{timestamp}.png"
        plt.savefig(plot_path)

        # Convert the 'percentage' column back to list for easier calculation
        percentage_list = percentage.tolist()

        # Create a DataFrame from the list
        final_percentage_df = pd.DataFrame({
            'time_point': range(len(percentage_list)),
            'percentage': percentage_list
        })

        # Export results
        percentage_results_path = f"./calculate_vacuoles_scripts/results_v3/{group}_percentages_for_{dataset_name}_{timestamp}.csv"
        final_percentage_df.to_csv(percentage_results_path, index=False)


    # Initialize an empty list to hold the individual DataFrames
    dfs = []

    # Use glob to find all CSV files that match the pattern
    csv_files = glob.glob(f"./calculate_vacuoles_scripts/results_v3/{group}_percentages_for_table_plot_backward_classes_*.csv")

    # Sort files to make sure they are concatenated in order
    csv_files.sort()

    # Loop through each file
    for i, csv_file in enumerate(csv_files):
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file)
    
        # Add a new column to identify the dataset
        df['dataset'] = i + 1

        # Append the DataFrame to the list
        dfs.append(df)

    # Concatenate all the DataFrames into a single DataFrame
    merged_df = pd.concat(dfs, ignore_index=True)

    # Save the merged DataFrame to a new CSV file
    merged_df.to_csv(f'./calculate_vacuoles_scripts/results_v3/{group}_merged_percentages.csv', index=False)


    # Read the merged CSV file
    merged_df = pd.read_csv(f'./calculate_vacuoles_scripts/results_v3/{group}_merged_percentages.csv')

    # Pivot the DataFrame to get it in the right format for a heatmap
    pivot_df = merged_df.pivot(index='dataset', columns='time_point', values='percentage')

    # Save the pivot DataFrame to a new CSV file
    pivot_df.to_csv(f'./calculate_vacuoles_scripts/results_v3/{group}_pivot_merged_percentages.csv', index=False)

    # Pivot the DataFrame to get it in the right format for a heatmap
    heatmap_data = merged_df.pivot(index='dataset', columns='time_point', values='percentage')

    # Create the heatmap
    fig, ax = plt.subplots(figsize=(15, 10))
    sns.heatmap(heatmap_data, cmap='inferno', vmin=0, vmax=30, square=True, cbar=False, ax=ax)

    # Customize the plot title and adjust its position
    plt.title(f'% of cells which duplicated bacterial area with respect\nto the mean of all previous time points - {group}')
    plt.subplots_adjust(top=1)
    # Display y-tick labels horizontally
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    # Create a custom color bar with specific height
    cbar_ax = fig.add_axes([0.92, 0.2, 0.03, 0.5])  # The dimensions [left, bottom, width, height] of the new axes.
    ColorbarBase(cbar_ax, cmap='inferno', orientation='vertical', ticks=[0, 10, 20, 30], label='Percentage')

    # Save the plot as PNG
    plot_path = f"./calculate_vacuoles_scripts/results_v3/heatmap_{group}.png"
    plt.savefig(plot_path)



print('ANALYSIS FINISHED')
