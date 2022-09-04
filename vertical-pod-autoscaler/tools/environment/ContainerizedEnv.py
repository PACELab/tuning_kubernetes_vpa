# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 12:59:39 2022

@author: mayukhdas
"""
import gym
import numpy as np
import gym.spaces as spaces
import pandas as pd
import dummy_env

class ContainerEnv(gym.Env):
    def __init__(self, num_micro=29, num_worker_nodes=1, num_tunable_parameters=200, num_request_types=3, max_episode_steps=1,**kwargs):
        #initilize env
         # set spaces
        #compute env bounds 
        # 1. Microservices 2. Node cPU & Mem ----
        self._max_episode_steps = max_episode_steps
        parameters_meta = pd.read_csv(kwargs["parameters_file"])
        self.args = kwargs["args"]

        self.num_micro=num_micro
        self.num_worker_nodes=num_worker_nodes
        self.num_tunable_parameters=num_tunable_parameters
        lb = [0.0]*(num_micro*2)
        lb.extend([0.0]*num_worker_nodes*2)
        lb.append(1) # RPS lower bound
        lb.append(1) #connnections lower bound
        lb.extend([0.0]*num_request_types)

        ub = [100.0]*(num_micro*2)
        ub.extend([100.0]*num_worker_nodes*2)
        ub.append(10000) #RPS upper bound
        ub.append(10000) #connections upper bound
        ub.extend([100.0]*num_request_types)
        
        self.observation_space = spaces.Box(low=np.array(lb),
                                            high=np.array(lb), 
                                            shape=(len(lb),), dtype=np.float32)
        

        #compute action bounds
        lba = parameters_meta["lower_limit"].values
        uba = parameters_meta["upper_limit"].values
        #-----------------should be changed------------
        self.action_space = spaces.Box(low=np.array(lba),
                                        high=np.array(uba), 
                                        shape=(len(lba),), dtype=np.float32)
        self.seed()
        super().__init__()

    def reset(self):
        self.current_step = 1
        #reset all values
        #print("reseting")
        self.state = self.observation_space.sample()
        return self.state
    
    def step(self,action):
        done=False
        reward = self._take_action(action)
        self.current_step += 1
        if self.current_step >= self._max_episode_steps:
            done=True
        obs = self._next_observation()
        return obs, reward, done , {}

    def _take_action(self,action):
        return dummy_env.take_action(action)
        #action is vector of all parameters 
        #call system function to apply changes to the containers etc. and return metrics
        
        
    def _next_observation(self):
        observation = dummy_env.next_observation()
        return observation
        ##call to system function -- return vector in the order 2*Microservices features + 2 node level features + other features
