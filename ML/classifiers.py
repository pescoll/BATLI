import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
from colorama import Fore, Style
import numpy as np


# classifiers.py

def plot_confusion_matrix(model, Xeval, yeval):
    ypred = model.predict(Xeval)
    cm = confusion_matrix(yeval, ypred, normalize='true')

    fig, ax = plt.subplots()
    sns.heatmap(100.*cm, annot=True, fmt='.1f', ax=ax, vmin=0., vmax=100., cmap='Reds')
    ax.set_xlabel('Predicted fates')
    ax.set_ylabel('True fates')
    ax.set_title('Confusion Matrix (%)')
    ax.xaxis.set_ticklabels(['Non replicative', 'Replicative'])
    ax.yaxis.set_ticklabels(['Non replicative', 'Replicative'])
    plt.tight_layout()
    return fig, ax  # Return the figure and axes

def scatter_plot(df, xfeature, yfeature, target_feature, xlabel, ylabel):
    x = df[xfeature]
    y = df[yfeature]
    rb = df[target_feature]
    colors = ['b', 'r']
    labels = [ 'non replicative', 'replicative']
    fig, ax = plt.subplots()
    for i in [0, 1]:
        ax.scatter(x[rb == i], y[rb == i], c=colors[i], edgecolors='k', label=labels[i])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    return ax

def plot_timeline(df_pos_avg, df_pos_std, df_neg_avg, df_neg_std, f, title, t_limit, ax):
    ax.plot(df_pos_avg['t'], df_pos_avg[f], 'r-', label='replicative')
    ax.fill_between(df_pos_avg['t'], df_pos_avg[f] - df_pos_std[f], df_pos_avg[f] + df_pos_std[f], color='r', alpha=0.2)
    ax.plot(df_neg_avg['t'], df_neg_avg[f], 'b-', label='non-repl.')
    ax.fill_between(df_neg_avg['t'], df_neg_avg[f] - df_neg_std[f], df_neg_avg[f] + df_neg_std[f], color='b', alpha=0.2)
    ax.legend(title=title)
    ax.set_xlim(min(df_pos_avg['t']), max(df_pos_avg['t']))
    yl = ax.get_ylim()
    ax.vlines(t_limit, yl[0], yl[1], 'k')
    ax.set_xlabel('time-point')
    return ax

def get_average(df, replicative=True):
    '''For the subset of data which is replicative or not, group all data by common time-point,
    then return the mean and std of the data frame rows grouped by time-points.'''
    sub_df = df.loc[df['rb'] == replicative]
    # Select numeric columns
    numeric_cols = sub_df.select_dtypes(include=[np.number]).columns.tolist()
    # Remove 't' from numeric_cols if it is in there
    if 't' in numeric_cols:
        numeric_cols.remove('t')
    # Perform groupby on 't' and compute mean and std on numeric columns
    df_avg = sub_df.groupby('t')[numeric_cols].mean().reset_index()
    df_std = sub_df.groupby('t')[numeric_cols].std().reset_index()
    return df_avg, df_std


def extract_data(df, tp):
    '''Extract from the loaded dataset the subset of data points we want to run
    the training and the assessment on. if tp is a list of time-points, then 
    the return dataset contains the average over specified time-points for each
    track. This requires the input dataset to have a "track_id" column.'''
    if type(tp) is list:
        return group_and_average(df, tp)
    else:
        early_data = df['t'] == tp
        ded = df[early_data]
        return ded


def group_by_time(df, tps):
    '''Extract from the loaded dataset the subset of data points we want to run
    the training and the assessment on.
    '''
    
    # Copy the dataframe.
    df_copy = df.copy()
    # All time-points in the dataframe, not in the input time-points.
    t_to_remove = set(df_copy.t.unique())
    t_to_remove.difference_update(set(tps))
    # Remove all timepoints that are not in the tps.
    for t in t_to_remove:
        df_copy.drop(df_copy[df_copy.t == t].index, inplace=True)
    return df_copy


def group_and_average(df, tps):
    '''Extract from the loaded dataset the subset of data points we want to run
    the training and the assessment on, by averaging over several time-points.
    '''

    if 'track_id' in df.columns:
        cell_lbl_feature = 'track_id'
    elif 'cell_lbl' in df.columns:
        cell_lbl_feature = 'cell_lbl'
    else:
        print(Fore.RED + 'Could not find a cell grouping column in the data frame ("track id" or "cell_lbl"). Aborting.' + Style.RESET)

    df_copy = group_by_time(df, tps)        

    # Group and average.
    df_avg = df_copy.groupby(cell_lbl_feature).mean()
    return df_avg


def group_and_median(df, tps):
    '''Extract from the loaded dataset the subset of data points we want to run
    the training and the assessment on, and take the median over sevearl time-points.
    '''

    if 'track_id' in df.columns:
        cell_lbl_feature = 'track_id'
    elif 'cell_lbl' in df.columns:
        cell_lbl_feature = 'cell_lbl'
    else:
        print(Fore.RED + 'Could not find a cell grouping column in the data frame ("track id" or "cell_lbl"). Aborting.' + Style.RESET)

    df_copy = group_by_time(df, tps)        

    # Group and average.
    df_median = df_copy.groupby(cell_lbl_feature).median()
    return df_median
