import numpy as np
import sys
import os
import pandas as pd
import random
from collections import OrderedDict

import helper


class PBR:
    def __init__(self, args, sequence_number, parameters_csv_path, delta=1, eta=1):
        self.args = args
        self.sequence_number = sequence_number
        self.parameters_csv_path = parameters_csv_path
        self.delta = delta
        self.eta = eta
        self.current_config_index = 0
        self.parameters_meta = self.generate_parameters_meta()
        self.x_current = self.init_point()

    def preprocess(self, config_values, default=False):
        """
        Format the init config according to the algorithms expectation
        1) scale all resources such that the range starts from single digit.
        """
        configs = []
        i = 0
        for _, row in self.parameters_meta.iterrows():
            # add index of categorical
            if row["type"] == "categorical":  # categorical
                # default value list already has indices for the categorical values
                value = config_values[i]
                if not default:
                    value = row["categorical_values"].index(value)
            else:
                # scale
                value = config_values[i]/row["step"]
            configs.append(value)
            i += 1
        return configs

    def init_point(self ):
        """
        Runs a set of initial points and selects the best of them for the algorithm to start with. This can be done
        using different sampling schemes or static samples.
        Returns a tuple <objective_value>,<List of config values>
        """
        if self.args.init:
            df = helper.get_init_points("numeric", self.sequence_number)
            # column corresponding to the minimum objective value
            best = df.iloc[-1, :].astype(float).idxmin()
            config_values = df[best].values
            init_point = helper.process_init_point(
                self.parameters_csv_path, config_values, dds=True)
            # changes to suit PBR
            scaled_init_point_x = self.preprocess(init_point[0])
        else:
            # get the default
            init_point, _ = helper.get_init_points_default()
            scaled_init_point = self.preprocess(init_point, default=True)
        return scaled_init_point

    def generate_parameters_meta(self):
        """
        Create metadata that will help the algorithm.
        """
        parameters_meta = pd.read_csv(self.parameters_csv_path)
        return parameters_meta

    def stop_config_generation(self, stats_file):
        """
        Signals the end of optimization
        """
        return self.current_config_index >= self.args.model_iterations

    def postprocess(self, x_next):
        """
        The config generated by the algorithm is converted to the format that is expected by the interfaces of the next
        stage. For example, for categorical values, we are just tuning the indices of the list of allowed values. That
        index has to be convered to the actual categorical value.
        """
        def check_range_and_adjust(value, lower_limit, upper_limit):
            if value < lower_limit:
                value = lower_limit
            if value > upper_limit:
                value = upper_limit
            return value

        configs = []
        index = 0
        for _, row in self.parameters_meta.iterrows():
            if row["type"] == "categorical":  # categorical
                # for categorical, the value being tuned is the rounded index in the list of allowed values
                # index 6 of the meta data structure has the list of allowed values
                rounded_index = round(x_next[index])
                rounded_index = check_range_and_adjust(
                    rounded_index, 0, len(row["categorical_values"]))
                configs.append(
                    row["categorical_values"][rounded_index])
            else:
                rescaled_value = x_next[index] * row["step"]
                if row["type"] == "discrete":  # discrete
                    rescaled_value = round(rescaled_value)
                rescaled_value = check_range_and_adjust(
                    rescaled_value, row["lower_limit"], row["upper_limit"])
                configs.append(rescaled_value)
            index += 1
        return configs

    def get_neighboring_rewards(self, u, plus=True):
        change = self.delta * u
        x_neighbour = (self.x_current +
                       change) if plus else (self.x_current - change)
        x_neighbour_config = self.postprocess(x_neighbour)
        #reward = helper.get_reward(self.args, x_neighbour_config, new_samples=plus)
        reward = random.randint(1,10)
        return reward

    def next_config(self):
        n = len(self.x_current)
        u = np.random.rand(1, n)
        u = (u/np.linalg.norm(u)).flatten()
        reward_plus = self.get_neighboring_rewards(u)
        reward_minus = self.get_neighboring_rewards(u, plus=False)
        x_next = self.x_current - \
            (self.eta/self.delta)*((reward_plus - reward_minus) /
                                   np.mean([reward_plus, reward_minus]))*u
        self.x_current = x_next
        return self.postprocess(x_next)

    def analysis(self, f_new):
        self.current_config_index += 1
        if self.current_config_index % 5 == 0:
            self.eta /= 2
        print("Reward %f" % f_new)


def test_f(configs):
    print(configs)
    return random.randint(1, 100)


if __name__ == "__main__":
    test_object = PBR(
        '/home/ubuntu/uservices/uservices-perf-analysis/configs/sn-all-temp/social_networking_parameters.csv', 1)
    while(not test_object.stop_config_generation("/dev/null")):
        configs = test_object.next_config()
        f_new = test_f(configs)
        test_object.analysis(f_new)
