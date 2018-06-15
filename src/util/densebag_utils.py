import logging
import os
import re
import pandas as pd
import numpy as np


logger = logging.getLogger("DenseBagBagger")


def get_latest_submission(folder):
    """
    Gets latest submission "to_submit_to_kaggle..." from given folder
    :param folder:
    :return: str filename of latest submission
    """
    all_files = os.listdir(folder)
    target_files = [f for f in all_files if f.startswith("to_submit_to_kaggle_")]

    def extract_timestamp(filename):
        result = re.sub('[^0-9]', '', filename)
        return int(result)
    target_files_sorted = sorted(target_files, key=lambda a: extract_timestamp(a))
    if len(target_files_sorted) == 0:
        logger.warning("No submission found in folder {}".format(folder))
        return ""
    return target_files_sorted[-1]


def get_files(base_path, prefix):
    """
    Returns submission files in basepath where model name starts with prefix.
    :param base_path: absolute or relative path
    :param prefix:
    :return: list of path for all files in folder that start with prefix
    """
    all_folders = os.listdir(os.path.join(base_path))
    target_folders = [f for f in all_folders if f.startswith(prefix)]
    return [os.path.join(os.path.join(base_path, folder),
            get_latest_submission(os.path.join(base_path, folder))) for folder in target_folders]


def get_dataframes_from_csv_list(files):
    """
    Opens all files in files and returns them as pd.DataFrame
    :param files:
    :return:
    """
    return [pd.read_csv(file) for file in files]


def get_average(list_df, column):
    """
    :param list_df:
    :param column:
    :return: the average of given column across all DataFrames in list
    """
    data = {i: list_df[i][column] for i in range(len(list_df))}
    df_all = pd.DataFrame(data)
    return np.mean(df_all, axis=1)


def sample_random_submission_files(n: int, base_path, prefix):
    all_submission_files = get_files(base_path, prefix)
    return np.random.choice(all_submission_files, size=n, replace=False)


def get_average_df_from_files(files):
    list_df = get_dataframes_from_csv_list(files)
    return pd.DataFrame(
        {
            'pitch': get_average(list_df, 'pitch'),
            'yaw': get_average(list_df, 'yaw')
        }
    )