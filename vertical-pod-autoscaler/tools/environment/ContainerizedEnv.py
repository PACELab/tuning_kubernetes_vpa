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
import vpa_env
import sn_env

class ContainerEnv(gym.Env):
    def __init__(self, num_micro=29, num_worker_nodes=1, num_tunable_parameters=200, num_request_types=3, max_episode_steps=1,**kwargs):
        #initilize env
         # set spaces
        #compute env bounds 
        # 1. Microservices 2. Node cPU & Mem ----
        self._total_steps = 0 # total steps across all episodes
        self._max_episode_steps = max_episode_steps
        parameters_meta = pd.read_csv(kwargs["parameters_file"])
        self.args = kwargs["args"]

        self.num_micro=num_micro
        self.num_worker_nodes=num_worker_nodes
        self.num_request_types = num_request_types
        self.num_tunable_parameters=num_tunable_parameters
        if self.args.experiment_type == "nginx":
            lb, ub = self.create_vpa_observation()
        elif self.args.experiment_type == "sn":
            lb, ub = self.create_sn_observation()           
        self.observation_space = spaces.Box(low=np.array(lb),
                                            high=np.array(ub), 
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

    def create_vpa_observation(self):
        lb = [0.0]*(self.num_micro*2)
        lb.extend([0.0]*self.num_worker_nodes*2)
        lb.append(0) # RPS lower bound
        lb.append(0) #connnections lower bound
        lb.extend([0.0]*self.num_request_types)
        ub = [100.0]*(self.num_micro*2)
        ub.extend([100.0]*self.num_worker_nodes*2)
        ub.append(20000) #RPS upper bound
        ub.append(10000) #connections upper bound
        ub.extend([100.0]*self.num_request_types)
        return (lb, ub)
    
    #TODO: take RPS, connections etc as kwargs and remove this.
    def create_sn_observation(self):
        lb = [0.0]*(self.num_micro*2)
        lb.extend([0.0]*self.num_worker_nodes*2)
        lb.append(0) # RPS lower bound
        lb.append(0) #connnections lower bound
        lb.extend([0.0]*self.num_request_types)
        ub = [100.0]*(self.num_micro*2)
        ub.extend([100.0]*self.num_worker_nodes*2)
        ub.append(500) #RPS upper bound
        ub.append(8) #connections upper bound
        ub.extend([100.0]*self.num_request_types)
        return (lb, ub)

    def reset(self):
        self.current_step = 1
        init_state = [0.0]*(self.num_micro*2)
        init_state.extend([0.0]*self.num_worker_nodes*2)
        init_state.append(0) # RPS lower bound
        init_state.append(0) #connnections lower bound
        init_state.extend([0.0]*self.num_request_types)
        self.state = init_state
        return self.state
    
    def step(self,action):
        done=False
        reward = self._take_action(action)
        self.current_step += 1
        self._total_steps += 1
        if self.current_step >= self._max_episode_steps:
            done=True
        obs = self._next_observation()
        return obs, reward, done , {}

    def _take_action(self,action):
        if self.args.experiment_type == "nginx":
            #action = dummy_env.take_action(self.args, self._total_steps, action)
            action = vpa_env.take_action(self.args, self._total_steps, action) 
        elif self.args.experiment_type == "vpa":
            action = sn_env.take_action(self.args, self._total_steps, action)
        else:
            action = dummy_env.take_action(self.args, self._total_steps, action)
        return action
        #action is vector of all parameters 
        #call system function to apply changes to the containers etc. and return metrics
        
        
    def _next_observation(self):
        if self.args.experiment_type == "nginx":
            observation = vpa_env.next_observation(self.args, self._total_steps)
        elif self.args.experiment_type == "vpa":
            observation = sn_env.next_observation(self.args, self._total_steps)
        else:
            observation = dummy_env.next_observation(self.args)
        return observation
        ##call to system function -- return vector in the order 2*Microservices features + 2 node level features + other features
