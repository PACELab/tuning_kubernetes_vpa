from vowpalwabbit import pyvw
import numpy as np
import pandas as pd
import sys
import os
import random
from collections import OrderedDict

import helper


class CBZO:
    def __init__(self, args , parameters_csv): 
        print(args)
        self.args = args
        self.parameters_csv_path = parameters_csv
        self.current_config_index = 0
        self.parameters_meta = self.generate_parameters_meta()
        self.n_actions = int(self.get_n_arms())
        self.vw = pyvw.vw('--cb_explore %d --first %d'%(self.n_actions, self.args.model_iterations//2))
        self.tunable_parameters = self.generate_tunable_parameters_list()
    
    def generate_parameters_meta(self):
        """
        Create metadata that will help the algorithm.
        Header: subsystem,parameter,type,lower_limit,upper_limit,categorical_values,default,step,units,prefix,comments 
        """
        parameters_meta = pd.read_csv(self.parameters_csv_path)
        return parameters_meta

    def get_n_arms(self):
        n_arms = 1
        for _, row in self.parameters_meta.iterrows():
            n_arms *= (row["upper_limit"] - row["lower_limit"]) // row["step"]
        return n_arms
    

    def generate_tunable_parameters_list(self):
        """
        This creates a list containing a subset of those parameters that are requested to be tuned. The parameters_csv
        also has parameters that are placeholders because of how the interfaces have been designed.
        """
        tunable_parameters = []
        for key in self.parameters_meta:
            # if any of the fields are set, that parameter is being tuned
            if any(self.parameters_meta[key]):
                tunable_parameters.append(key)
        return tunable_parameters

    def stop_config_generation(self, stats_file):
        """
        Signals the end of optimization
        """
        return self.current_config_index >= self.args.model_iterations

    def postprocess(self):
        """
        The algorithm returns an index. 
        Return the ith element in the cross-product of all the different values of each parameter.
        P1 ={p1c1,p1c2,p1c3} P2={p2c1,p2c2}
        P1*P2 = {{p1c1,p2c1}......}
        """

        index = self.action
        reversed_params_meta_df = self.parameters_meta[::-1].reset_index(drop=True) # O(1) op
        configs = [None] * len(reversed_params_meta_df)
        i = len(reversed_params_meta_df) - 1
        for _, row in reversed_params_meta_df.iterrows():
            n_values = (row["upper_limit"] - row["lower_limit"]) // row["step"] 
            position = self.action % n_values
            configs[i] = row["lower_limit"] + position * row["step"]
            if configs[i] > row["upper_limit"]:
                configs[i] = row["upper_limit"] 
            index = index // n_values
            i -= 1
        return configs

    def next_config(self):
        ex = self.vw.parse(' | c1:1')
        pred = self.vw.predict(ex)
        self.vw.finish_example(ex)

        # Due to large number of parameters, the sum of probabilities exceeds 1.
        # Normalize again so that np.random.choice doesn't complain. 
        pred = [i/sum(pred) for i in pred]

        self.action  = np.random.choice(self.n_actions, p=pred)
        self.pdf_current_action = pred[self.action]
        return self.postprocess()

    def analysis(self, f_new):
        self.current_config_index += 1
        #cost = abs(self.optimal_action - f_new)
        #cost function is already a positive value that has to be minimized
        ex = self.vw.parse('ca {}:{}:{} | c1:1'.format(self.action, f_new, self.pdf_current_action))
        self.vw.learn(ex)
        self.vw.finish_example(ex)
        print("Reward %f" % f_new)


def test_f(configs):
    print(configs)
    return random.randint(1, 100)


if __name__ == "__main__":
    test_object = CBZO(
        '/home/ubuntu/uservices/uservices-perf-analysis/configs/sn-all-temp/social_networking_parameters.csv', 1)
    while(not test_object.stop_config_generation("/dev/null")):
        configs = test_object.next_config()
        f_new = test_f(configs)
        test_object.analysis(f_new)

