import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ks_2samp
from scipy.stats import mannwhitneyu
from statsmodels.stats.proportion import proportions_ztest
import datetime

# Load the data
df = pd.read_csv('./vacuole_growth_script/MD28_29_30_pooled_deltas copy.csv')  # replace with your file path

# Filter the DataFrame
df_filtered = df[df['rb'] == 1]

# Sorting by cell_lbl and t, to ensure the time series for each cell is in correct order
df_sorted = df_filtered.sort_values(['cell_lbl', 't'])

# Doubling factor, adjust this value as per your requirements
double_factor = 2 

# # Function to calculate duplication including current row
# def calculate_duplication(group):
#     group['duplication'] = (group['bacteria_area_[um²]-_sum_per_cell_'] >= double_factor * group['bacteria_area_[um²]-_sum_per_cell_'].expanding().mean()).astype(int)
#     return group

# Function to calculate duplication not including current row
def calculate_duplication(group):
    # Shift the series down by one and then calculate expanding mean
    shifted_series = group['legio_area'].shift(1)
    group['duplication'] = (group['legio_area'] >= double_factor * shifted_series.expanding().mean()).astype(int)
    return group

# Applying the function to each group
df_final = df_sorted.groupby('cell_lbl').apply(calculate_duplication)

# Save file
timestamp = datetime.datetime.now().strftime("%d%m%y-%H%M%S")
results_path = f"./vacuole_growth_script/results_{timestamp}.csv"
df_final.to_csv(results_path, index=False)

# Print the number of unique cell_IDs
print("Number of unique cell_IDs:", df_final['cell_lbl'].nunique())

# Filter the cells that have duplication=1
df_duplication = df_final[df_final['duplication'] == 1]

# For each unique cell_lbl, find the first time point where duplication=1
first_duplication = df_duplication.groupby('cell_lbl')['t'].min()

# Count the occurrences of each time point
time_counts = first_duplication.value_counts()

# Find the time point with the maximum count
max_time_point = time_counts.idxmax()
print(f"The time point at which most unique cells start to be duplication=1 is: {max_time_point}")

# Create a dictionary to store the results
results = {}

# For each unique time point, calculate the z-score and p-value
for time_point in first_duplication.unique():
    count = time_counts[time_point]
    nobs = len(first_duplication)
    value = 1/len(time_counts)  # expected proportion

    z_stat, p_val = proportions_ztest(count, nobs, value)

    # Determine the significance level
    if p_val < 0.0001:
        significance = "(****)"
    elif p_val < 0.001:
        significance = "(***)"
    elif p_val < 0.01:
        significance = "(**)"
    elif p_val < 0.05:
        significance = "(*)"
    else:
        significance = ""

    # Store the results in the dictionary
    results[time_point] = (p_val, significance)

# Sort the results by the time point and print them
for time_point in sorted(results.keys()):
    p_val, significance = results[time_point]
    print(f"Time point: {time_point}, p-value: {p_val} {significance}")

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
plt.savefig('./vacuole_growth_script/bar_graph.png')


# Convert the 'percentage' column back to list for easier calculation
percentage_list = percentage.tolist()

# Create a DataFrame from the list
final_percentage_df = pd.DataFrame({
    'time_point': range(len(percentage_list)),
    'percentage': percentage_list
})
percentage_results_path = f"./vacuole_growth_script/percentage_results_{timestamp}.csv"
final_percentage_df.to_csv(percentage_results_path, index=False)

# # Size of the rolling window
# window_size = 3

# print('LOOP KS')

# # For each time point, starting from the second one
# for i in range(window_size, len(percentage_list)):
#     # Previous percentages (use a rolling window)
#     prev_percentages = percentage_list[i - window_size:i]
#     # Current percentage
#     curr_percentage = [percentage_list[i]]  # Must be a list for the test

#     # Perform Kolmogorov-Smirnov test
#     ks_stat, p_val = ks_2samp(prev_percentages, curr_percentage)

#     # Print the time point and p-value
#     print(f"Time point: {i}, p-value: {p_val}")

#     # If p-value is less than 0.05, break the loop
#     if p_val < 0.05:
#         print(f"(*) Time point: {i}, p-value: {p_val}")
#         break

# # If loop completed all iterations, print a message
# else:
#     print("KS: All time points processed.")

# print('LOOP MW')

# from scipy.stats import mannwhitneyu

# # For each time point, starting from the second one
# for i in range(window_size, len(percentage_list)):
#     # Previous percentages (use a rolling window)
#     prev_percentages = percentage_list[i - window_size:i]
#     # Current percentage
#     curr_percentage = [percentage_list[i]]  # Must be a list for the test

#     # Perform Mann-Whitney U test
#     u_stat, p_val = mannwhitneyu(prev_percentages, curr_percentage, alternative='two-sided')

#     # Print the time point and p-value
#     print(f"Time point: {i}, p-value: {p_val}")

#     # If p-value is less than 0.05, print the time point and p-value
#     if p_val < 0.05:
#         print(f"Time point: {i}, p-value: {p_val}")
#         break

# # If loop completed all iterations, print a message
# else:
#     print("MW: All time points processed.")


print('FINISHED')

# # Print % list
# print(percentage_list)

# # Print the first 20 rows of the filtered DataFrame
# print(df_final.head(20))