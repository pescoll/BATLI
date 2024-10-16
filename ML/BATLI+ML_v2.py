# Imports.
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from classifiers import get_average
from classifiers import plot_timeline
from classifiers import extract_data
from classifiers import scatter_plot
from classifiers import group_and_average
from classifiers import plot_confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import (
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    average_precision_score
)
from sklearn.calibration import calibration_curve
from matplotlib import rcParams


# Data file.
test_file = '/Users/pedro/Documents/ML/MD28_29_30_pooled_deltas.csv'
# Features in the input data we use:
features = ['delta_redsdmean', 'delta_farredsdmean', 'delta_farredmean']
feature_labels = ['TMRM sd/mean', 'CellROX sd/mean', 'CellROX mean']
selected_features_index = [0, 1]  # Indices for TMRM sd/mean and CellROX sd/mean
selected_features = [features[i] for i in selected_features_index]

# Time limit to be predictive.
t_limit = 5  # time-point

# The fraction of training data in the training data / eval data resampling.
fraction = 0.25

# Load data, split it in replicative vs non-replicative groups.
df = pd.read_csv(test_file)
df_pos_avg, df_pos_std = get_average(df, True)
df_neg_avg, df_neg_std = get_average(df, False)

# Plot mean over time for each group.
sns.set()  # Beautify plots.
fig, axs = plt.subplots(1, 2, figsize=(20, 8))  # Create 2 subplots side by side.
for ip, i in enumerate(selected_features_index):
    plot_timeline(df_pos_avg, df_pos_std, df_neg_avg, df_neg_std,
                  features[i], feature_labels[i], t_limit, axs[ip])
plt.tight_layout()
plt.show()

# Extract data at time t.
t = 5
target_feature = 'rb'  # The name of the replicative yes/no feature.
ded1 = extract_data(df, t)
sns.set()
ix = selected_features_index[0]
iy = selected_features_index[1]
scatter_plot(ded1, features[ix], features[iy], target_feature,
             feature_labels[ix], feature_labels[iy])

# Average over time-points for each cell separately.
ts = range(0, 5)  # From time-point 0 to N inclusive.
ded2 = group_and_average(df, ts)
sns.set()
scatter_plot(ded2, features[ix], features[iy], target_feature,
             feature_labels[ix], feature_labels[iy])

# Get numerical data to train and test on.
X = ded2[selected_features].values
y = ded2['rb'].values

# Split training and test data.
print('Splitting dataset into training and testing datasets')
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=fraction, random_state=16)
print('There are %3d non-replicative and %3d replicative cells in the training dataset.' %
      (sum(y_train == 0), sum(y_train == 1)))
print('There are %3d non-replicative and %3d replicative cells in the test dataset.' %
      (sum(y_test == 0), sum(y_test == 1)))

# Build the model.
print('Starting the training of the model')
model = make_pipeline(
    StandardScaler(),
    LogisticRegression(random_state=123, class_weight='balanced')
)

# Fit model.
model.fit(X_train, y_train)
print('Training finished')

# Basic classification scores.
score_train = model.score(X_train, y_train)
score_test = model.score(X_test, y_test)

# AUROC.
prob_train = model.predict_proba(X_train)[:, 1]  # Probability of the positive class
prob_test = model.predict_proba(X_test)[:, 1]
# ROC score
auroc_score_train = roc_auc_score(y_train, prob_train)
auroc_score_test = roc_auc_score(y_test, prob_test)

print('Found training score of %.2f and a test score of %.2f.\nAUROC for training data and test data: %.2f and %.2f' %
      (score_train, score_test, auroc_score_train, auroc_score_test))

# Confusion matrix.
fig_cm, ax_cm = plot_confusion_matrix(model, X_test, y_test)

# Save the confusion matrix figure
fig_cm.savefig('confusion_matrix.png', format='png', dpi=300)
plt.show()  # Display the plot if desired

# AUROC
fpr, tpr, _ = roc_curve(y_test, prob_test)
fig_auroc, ax_auroc = plt.subplots()
ax_auroc.plot(fpr, tpr, label="Logistic Regression (AUC = %.2f)" % auroc_score_test)
ax_auroc.plot([0, 1], [0, 1], linestyle='--', color='gray')
ax_auroc.legend(loc='lower right')
ax_auroc.set_xlabel('False Positive Rate')
ax_auroc.set_ylabel('True Positive Rate')
ax_auroc.set_title('Receiver Operating Characteristic (ROC) Curve')
plt.tight_layout()

# Save the AUROC figure
fig_auroc.savefig('auroc.png', format='png', dpi=300)
plt.show()

# Extract the scaler and classifier from the pipeline
scaler = model.named_steps['standardscaler']
classifier = model.named_steps['logisticregression']

# Extract coefficients
intercept = classifier.intercept_[0]
coef = classifier.coef_[0]
print("Intercept (β₀):", intercept)
print("Coefficients (β):", coef)

# Prepare the logistic regression equation in LaTeX format
feature_names = [feature_labels[i] for i in selected_features_index]
# Escape underscores in feature names for LaTeX
feature_names_latex = [name.replace('_', r'\_') for name in feature_names]

# Start constructing the equation, escaping curly braces
equation = r"$P = \dfrac{{1}}{{1 + e^{{- \left( {:.4f}".format(intercept)
for c, fname in zip(coef, feature_names_latex):
    sign = ' + ' if c >= 0 else ' - '
    equation += r"{} {:.4f} \times \mathrm{{{}}}".format(sign, abs(c), fname)
equation += r"\right)}}}$"

# Display and save the equation as an image
fig_eq, ax_eq = plt.subplots(figsize=(12, 1))
ax_eq.axis('off')
ax_eq.text(0.5, 0.5, equation, fontsize=18, ha='center', va='center')
plt.tight_layout()
fig_eq.savefig('logistic_regression_equation.png', dpi=300, bbox_inches='tight')
plt.show()

# Compute precision-recall curve
precision, recall, thresholds = precision_recall_curve(y_test, prob_test)
avg_precision = average_precision_score(y_test, prob_test)

# Calculate the no-skill line (baseline precision)
no_skill = y_test.sum() / len(y_test)  # Proportion of positive class in y_test

# Plot the precision-recall curve
fig_pr, ax_pr = plt.subplots(figsize=(6, 5))
ax_pr.plot(recall, precision, label=f'Logistic Regression Model')

# Plot the no-skill line
ax_pr.hlines(y=no_skill, xmin=0, xmax=1, linestyles='dashed', colors='gray', label='No Skill')

# Plot the perfect model line as a square
ax_pr.plot([0, 1, 1], [1, 1, 0], linestyle='--', color='red', label='Perfect Model')


ax_pr.set_xlabel('Recall')
ax_pr.set_ylabel('Precision')
ax_pr.set_title('Precision-Recall Curve')
ax_pr.legend(loc='lower left')
plt.tight_layout()
fig_pr.savefig('precision_recall_curve.png', dpi=300)
plt.show()

