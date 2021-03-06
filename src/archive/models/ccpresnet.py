"""Example architecture."""
from typing import Dict

import tensorflow as tf

import util.gaze
from core import BaseDataSource
from models.custom import CustomModel
import logging


data_format = "channels_last"  # Change this to "channels_first" to run on GPU
logger = logging.getLogger(__name__)


class CCPResNet(CustomModel):
    """An example neural network architecture."""

    def get_optimizer(self, spec):
        return tf.train.GradientDescentOptimizer(
            learning_rate=spec['learning_rate'],
        )

    def get_identifier(self):
        return "CCPResNet"

    def build_model(self, data_sources: Dict[str, BaseDataSource], mode: str):
        """Build model."""
        data_source = next(iter(data_sources.values()))
        input_tensors = data_source.output_tensors

        logger.info("input_tensors.keys(): "+str(input_tensors.keys()))  # eye, gaze, head

        x = input_tensors['eye']
        y = input_tensors['gaze']

        # # only augment if training
        if mode == tf.estimator.ModeKeys.TRAIN:
            with tf.variable_scope('augmentation'):
                x, y = self.augment_x(x, y, add_noise=False)

        # Trainable parameters should be specified within a known `tf.variable_scope`.
        # This tag is later used to specify the `learning_schedule` which describes when to train
        # which part of the network and with which learning rate.
        #
        # This network has two scopes, 'conv' and 'fc'. Though in practise it makes little sense to
        # train the two parts separately, this is possible.
        with tf.variable_scope('conv'):
            with tf.variable_scope('res1'):
                x_input = x
                x = self.get_conv2d("conv1_64_1", x, filters=64, padding="same", data_format=data_format, activation=tf.nn.relu)
                x = self.get_conv2d("conv1_64_2", x, filters=64, padding="valid", data_format=data_format, activation=tf.nn.relu)

                x = self.get_max_pooling2d("maxpool_64", x, pool_size=2, strides=2, padding="valid", data_format=data_format)

                x = self.get_residual_block(x_input, x)

            with tf.variable_scope('res2'):
                x_input = x
                x = self.get_conv2d("conv1_128_1", x, filters=128, padding="same", data_format=data_format,
                                    activation=tf.nn.relu)
                x = self.get_conv2d("conv1_128_2", x, filters=128, padding="valid", data_format=data_format,
                                    activation=tf.nn.relu)

                x = self.get_max_pooling2d("maxpool_128", x, pool_size=2, strides=2, padding="valid",
                                       data_format=data_format)
                x = self.get_residual_block(x_input, x)

            with tf.variable_scope('res3'):
                x_input = x
                x = self.get_conv2d("conv1_256_1", x, filters=256, padding="same", data_format=data_format,
                                    activation=tf.nn.relu)
                x = self.get_conv2d("conv1_256_2", x, filters=256, padding="valid", data_format=data_format,
                                    activation=tf.nn.relu)

                x = self.get_max_pooling2d("maxpool_256", x, pool_size=2, strides=2, padding="valid",
                                           data_format=data_format)
                x = self.get_residual_block(x_input, x)

        with tf.variable_scope('fc'):
            # Flatten the 50 feature maps down to one vector
            x = tf.contrib.layers.flatten(x)

            # FC layer
            x = tf.layers.dense(x, units=1024, name='fc1_1024', activation=tf.nn.tanh)
            self.summary.histogram('fc1_1024/activations', x)

            # with tf.variable_scope('dropout'):
            #     x = tf.layers.dropout(x, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)

            # Directly regress two polar angles for gaze direction
            x = tf.layers.dense(x, units=2, name='fc2_2')
            self.summary.histogram('fc2_2/activations', x)

        # Define outputs
        with tf.variable_scope('mse'):  # To optimize
            loss_terms = {
                'gaze_mse': tf.reduce_mean(tf.squared_difference(x, y)),
            }
        with tf.variable_scope('ang'):  # To evaluate in addition to loss terms
            metrics = {
                'gaze_angular': util.gaze.tensorflow_angular_error_from_pitchyaw(x, y),
            }
        return {'gaze': x}, loss_terms, metrics


class GaussianCCPResnet(CustomModel):
    def build_model(self, data_sources: Dict[str, BaseDataSource], mode: str):
        """Build model."""
        data_source = next(iter(data_sources.values()))
        input_tensors = data_source.output_tensors

        logger.info("input_tensors.keys(): " + str(input_tensors.keys()))  # eye, gaze, head

        x = input_tensors['eye']
        y = input_tensors['gaze']

        # # only augment if training
        if mode == tf.estimator.ModeKeys.TRAIN:
            with tf.variable_scope('augmentation'):
                x, y = self.augment_x(x, y, add_noise=False)

        # Trainable parameters should be specified within a known `tf.variable_scope`.
        # This tag is later used to specify the `learning_schedule` which describes when to train
        # which part of the network and with which learning rate.
        #
        # This network has two scopes, 'conv' and 'fc'. Though in practise it makes little sense to
        # train the two parts separately, this is possible.

        # with tf.variable_scope("global_scope", initializer=tf.truncated_normal_initializer(mean=0, stddev=0.01)):
        with tf.variable_scope('conv', initializer=tf.truncated_normal_initializer(mean=0, stddev=0.01)):
            with tf.variable_scope('res1'):
                x_input = x
                x = self.get_conv2d("conv1_64_1", x, filters=64, padding="same", data_format=data_format,
                                    activation=tf.nn.relu)
                x = self.get_conv2d("conv1_64_2", x, filters=64, padding="valid", data_format=data_format,
                                    activation=tf.nn.relu)

                x = self.get_max_pooling2d("maxpool_64", x, pool_size=2, strides=2, padding="valid",
                                           data_format=data_format)

                x = self.get_residual_block(x_input, x)

            with tf.variable_scope('res2'):
                x_input = x
                x = self.get_conv2d("conv1_128_1", x, filters=128, padding="same", data_format=data_format,
                                    activation=tf.nn.relu)
                x = self.get_conv2d("conv1_128_2", x, filters=128, padding="valid", data_format=data_format,
                                    activation=tf.nn.relu)

                x = self.get_max_pooling2d("maxpool_128", x, pool_size=2, strides=2, padding="valid",
                                           data_format=data_format)
                x = self.get_residual_block(x_input, x)

            with tf.variable_scope('res3'):
                x_input = x
                x = self.get_conv2d("conv1_256_1", x, filters=256, padding="same", data_format=data_format,
                                    activation=tf.nn.relu)
                x = self.get_conv2d("conv1_256_2", x, filters=256, padding="valid", data_format=data_format,
                                    activation=tf.nn.relu)

                x = self.get_max_pooling2d("maxpool_256", x, pool_size=2, strides=2, padding="valid",
                                           data_format=data_format)
                x = self.get_residual_block(x_input, x)

        with tf.variable_scope('fc', initializer=tf.truncated_normal_initializer(mean=0, stddev=0.01)):
            # Flatten the 50 feature maps down to one vector
            x = tf.contrib.layers.flatten(x)

            # FC layer
            x = tf.layers.dense(x, units=1024, name='fc1_1024', activation=tf.nn.tanh)
            self.summary.histogram('fc1_1024/activations', x)

            # with tf.variable_scope('dropout'):
            #     x = tf.layers.dropout(x, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)

            # Directly regress two polar angles for gaze direction
            x = tf.layers.dense(x, units=2, name='fc2_2')
            self.summary.histogram('fc2_2/activations', x)

        # Define outputs
        with tf.variable_scope('mse'):  # To optimize
            loss_terms = {
                'gaze_mse': tf.reduce_mean(tf.squared_difference(x, y)),
            }
        with tf.variable_scope('ang'):  # To evaluate in addition to loss terms
            metrics = {
                'gaze_angular': util.gaze.tensorflow_angular_error_from_pitchyaw(x, y),
            }
        return {'gaze': x}, loss_terms, metrics

        # def get_identifier(self):
        #     return "GaussianCCPResNet"
        #
        # def build_model(self, data_sources: Dict[str, BaseDataSource], mode: str):
        #     return super(GaussianCCPResnet, self).build_model(data_sources, mode)
        #     # return_value = {}
        #     # with tf.variable_scope("global_scope", initializer=tf.truncated_normal_initializer(mean=0, stddev=0.01)):
        #     #     return_value = super(GaussianCCPResnet, self).build_model(data_sources, mode)
        #     # return return_value
