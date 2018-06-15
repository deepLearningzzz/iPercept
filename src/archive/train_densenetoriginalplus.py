#!/usr/bin/env python3
"""Main script for training a model for gaze estimation."""
import argparse

import coloredlogs
import tensorflow as tf

from models.densenet_original_plus import DenseNetOriginalPlus

Model = DenseNetOriginalPlus

DEBUG = False
if DEBUG:
    NUM_EPOCHS = 6
else:
    NUM_EPOCHS = 250
    # NUM_EPOCHS = 10

# 35 epochs with LR=0.1
# some epochs with LR=0.01.observation: more overfitting. action: reduce batch size to 64, set LR back to 0.1
# some epochs with BS=64 and LR=0.01
# at 50 epochs: LR=0.004 and Batch_SIZE=32
# at 43.5K steps: batch size 128 (because neither train nor test loss changed) -> had to set epochs to 150

LEARNING_RATE = 0.004 #04  # todo: implement dynamic way to divide this after some epochs
BATCH_SIZE = 128  # original 64 or 256

tf.set_random_seed(5)

if __name__ == '__main__':

    # Set global log level
    parser = argparse.ArgumentParser(description='Train a gaze estimation model.')
    parser.add_argument('-v', type=str, help='logging level', default='info',
                        choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = parser.parse_args()
    coloredlogs.install(
        datefmt='%d/%m %H:%M',
        fmt='%(asctime)s %(levelname)s %(message)s',
        level=args.v.upper(),
    )

    # Initialize Tensorflow session
    tf.logging.set_verbosity(tf.logging.INFO)
    gpu_options = tf.GPUOptions(allow_growth=True)
    with tf.Session(config=tf.ConfigProto(gpu_options=gpu_options)) as session:

        # Declare some parameters
        batch_size = BATCH_SIZE

        # Define model
        from datasources import HDF5Source

        model = Model(
            # Tensorflow session
            # Note: The same session must be used for the model and the data sources.
            session,

            # The learning schedule describes in which order which part of the network should be
            # trained and with which learning rate.
            #
            # A standard network would have one entry (dict) in this argument where all model
            # parameters are optimized. To do this, you must specify which variables must be
            # optimized and this is done by specifying which prefixes to look for.
            # The prefixes are defined by using `tf.variable_scope`.
            #
            # The loss terms which can be specified depends on model specifications, specifically
            # the `loss_terms` output of `BaseModel::build_model`.
            learning_schedule=[
                {
                    'loss_terms_to_optimize': {
                        'gaze_mse': ['denseblocks', 'regression'],
                    },
                    'metrics': ['gaze_angular'],
                    'learning_rate': LEARNING_RATE,
                },
            ],

            test_losses_or_metrics=['gaze_mse', 'gaze_angular'],

            # Data sources for training and testing.
            train_data={
                'real': HDF5Source(
                    session,
                    batch_size,
                    hdf_path='../datasets/MPIIGaze_kaggle_students.h5',
                    keys_to_use=['train'],
                    min_after_dequeue=100,
                ),
            },
            test_data={
                'real': HDF5Source(
                    session,
                    batch_size,
                    hdf_path='../datasets/MPIIGaze_kaggle_students.h5',
                    keys_to_use=['validation'],
                    testing=True,
                ),
            },
        )

        # Train this model for a set number of epochs
        model.train(
            num_epochs=NUM_EPOCHS,
        )

        # Evaluate for Kaggle submission
        model.evaluate_for_kaggle(
            HDF5Source(
                session,
                batch_size,
                hdf_path='../datasets/MPIIGaze_kaggle_students.h5',
                keys_to_use=['test'],
                testing=True,
            )
        )
