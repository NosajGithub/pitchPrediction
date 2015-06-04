import argparse
import datetime
import os
import pickle

import numpy as np
import pandas as pd

from sklearn import cross_validation

from .features import *
from .utils import *
from .validation import *


def run(train, test, **kwargs):
    """Build machine learning model for pitch prediction.

    Args:
        train (filepath): Complete file path including name of file.
        test (filepath): Complete file path including name of file, should match train columns.
    Returns:
        model (object): Pandas dataframe with header.
        results (dataframe): Pandas dataframe with header.
    """
    # some_option = kwargs.get('some_option', 'some_value')

    train_df = pd.read_csv(args.train)
    test_df = pd.read_csv(args.test)

    # TODO: apply feature extraction and transformation

    # TODO: automatic feature selection

    # TODO: ensemble sklearn models

    return None, None


if __name__ == '__main__':
    # Parse command line parameters
    parser = argparse.ArgumentParser(description='Train models locally for Predicting The Next Pitch')
    parser.add_argument('--train', required=True, help="CSV file for training dataset.")
    parser.add_argument('--test', required=True, help="CSV file for test dataset.")
    parser.add_argument('--logs-dir', default='logs/', help="Name of directory to save logs.")
    parser.add_argument('--models-dir', default='models/', help="Name of directory to save output models.")
    parser.add_argument('--output-dir', default='data/output/', help="Name of directory for saving output csv(s).")
    args = parser.parse_args()

    # python main.py --train='data/input/train.csv' --test='data/input/test.csv'
    try:
        # TODO: add log of successful model building to args.logs_dir
        model, results = run(args.train, args.test)
    except:
        # TODO: add log of error to args.logs_dir
        pass

    model_name = 'some_model'
    filename = model_name + '-' + datetime.date.today().strftime('%Y%m%dT%H:%M:%S')

    # Save predictions and persist model for later
    results.to_csv(os.path.realpath(__file__) + args.output_dir + filename + '.csv', index=False)
    with open(os.path.realpath(__file__) + args.models_dir + filename + '.pkl', 'wb')
        pickle.dump(mydict, model)
