#! /usr/bin/python3
"""
pip install scikit-optimize
"""
from skopt.utils import use_named_args
from skopt import gp_minimize, gbrt_minimize, forest_minimize
from timeit import default_timer as timer
import os
import sys

import helper


class BayesianOptimization:
    # Initialize all the private variables.
    def __init__(self, args,  current_model_iteration=-1):
        self.args = args
        # index of the current configuration. -1 before the method starts.
        self.current_model_iteration = current_model_iteration
        # domain space for BO using skopt library. verison and app code are the input
        self.domain_space = helper.skopt_space()
        self.surrogate_model = {"gp": gp_minimize, "gbrt": gbrt_minimize,
                                "forest": forest_minimize}[args.approach.split('-')[1]]
        self.total_time = 0

    def optimize(self):
        # get the domain space for the hyperparameters
        space = self.domain_space[0]
        start_time = None
        end_time = None

        # objective function as a nested function
        # use this decorator to correctly receive the parameters as a list

        @use_named_args(space)
        def objective(**hyperparameters):
            # uses the variable of the nesting function
            nonlocal start_time
            # roughly the end of the previous iteration
            end_time = timer()
            self.total_time = end_time - start_time
            config = []
            paramOrder = self.domain_space[1]
            # creating config with ordered parameters
            for param in paramOrder:
                if param not in hyperparameters:
                    config.append(None)
                else:
                    config.append(hyperparameters[param])

            # a new config has been created by the optimization method
            self.current_model_iteration += 1

            objective_function_value = helper.get_reward(self.args, self.current_model_iteration,
                                                         config)

            start_time = timer()
            return objective_function_value

        start_time = timer()
        x_0 = []
        y_0 = []
        if self.args.init_default:
                x, y = helper.get_init_points_default()
                x_0.append(x)
                y_0.append(y)
                result = self.surrogate_model(objective, space, n_calls=self.args.model_iterations,
                                              n_initial_points=1, x0=x_0, y0=y_0, acq_func=self.args.acq_func)
        else:
                result = self.surrogate_model(
                    objective, space, n_calls=self.args.model_iterations, n_initial_points=3, acq_func=self.args.acq_func)


        print("Optimization time per iteration %f" %
              (self.total_time/self.args.model_iterations))
        return result
