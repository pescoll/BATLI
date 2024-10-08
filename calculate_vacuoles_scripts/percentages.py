
import pandas as pd
import numpy as np

# List of dataset paths
dataset_paths = [
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_WT_8_cleaned_dataset_MD_06_Measurement_1_Evaluation4_Population_-_tracked_cells.csv',
    './calculate_vacuoles_scripts/datasets/table_plot_backward_classes_NI_7_cleaned_dataset_MD_07_Measurement_1_Evaluation1_Population_-_tracked_cells.csv',
    '',
    ''
]

# Function to calculate percentages
def calculate_percentage(value, total):
    return (value / total) * 100

# Function to process a dataset
def process_dataset(dataset_path):
    # Read the CSV dataset
    df = pd.read_csv(dataset_path)
    
    # Filter to t=0
    t0_df = df[df['t'] == 0]
    
    # Count entries in t=0 dataset
    n = len(t0_df)
    
    # Count entries in 'if' column if=1
    infected = len(t0_df[t0_df['infected'] == 1])
    
    # Calculate % infected
    percent_infected = calculate_percentage(infected, n)
    
    # Count entries in 'growth' column growth=1
    replicative = len(t0_df[t0_df['growth'] == 1])
    
    # Calculate % replicative
    percent_replicative = calculate_percentage(replicative, infected)
    
    # Return results summary
    return (n, infected, percent_infected, replicative, percent_replicative)

# Process each dataset
dataset_summaries = []
for dataset_number, dataset_path in enumerate(dataset_paths, 1):
    if dataset_path.strip():  # Check if path is not empty
        dataset_summary = process_dataset(dataset_path)
        dataset_summaries.append(dataset_summary)
        # Print results summary
        print(f"Dataset {dataset_number}:")
        print(f"n = {dataset_summary[0]}")
        print(f"infected = {dataset_summary[1]}")
        print(f"% infected = {dataset_summary[2]:.2f}%")
        print(f"replicative = {dataset_summary[3]}")
        print(f"% replicative = {dataset_summary[4]:.2f}%")
        print()

# Calculate total summary
n_total = sum([summary[0] for summary in dataset_summaries])
infected_total = sum([summary[1] for summary in dataset_summaries])
percent_infected_mean = np.mean([summary[2] for summary in dataset_summaries])
percent_infected_sd = np.std([summary[2] for summary in dataset_summaries])
replicative_total = sum([summary[3] for summary in dataset_summaries])
percent_replicative_mean = np.mean([summary[4] for summary in dataset_summaries])
percent_replicative_sd = np.std([summary[4] for summary in dataset_summaries])

# Print total summary
print("Datasets TOTAL:")
print(f"n = {n_total}")
print(f"infected = {infected_total}")
print(f"% infected = {percent_infected_mean:.2f} +/- {percent_infected_sd:.2f}%")
print(f"replicative = {replicative_total}")
print(f"% replicative = {percent_replicative_mean:.2f} +/- {percent_replicative_sd:.2f}%")

# Create a DataFrame for the results
results_df = pd.DataFrame(dataset_summaries, columns=['n', 'infected', '% infected', 'replicative', '% replicative'])

# Export results to CSV
results_df.to_csv('./calculate_vacuoles_scripts/results/percentages_at_t_0.csv', index=False)
