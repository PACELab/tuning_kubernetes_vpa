# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 12:59:39 2022

@author: mayukhdas
"""
import gym
import numpy as np
import gym.spaces as spaces
import math

class DummyContainerEnvCont(gym.Env):
    def __init__(self, num_features=1, num_tunable_parameters=1):
        #initilize env
         # set spaces
        #compute env bounds 
        self._max_episode_steps = 1
        self.num_features=num_features
        self.num_tunable_parameters=num_tunable_parameters
        # 1. Microservices 2. Node cPU & Mem ---- 
        # lb = [0.0]*(num_micro*2)
        # lb = lb.extend([0.0]*num_worker_nodes*2)

        # ub = [1.0]*(num_micro*2)
        # ub = ub.extend([1.0]*num_worker_nodes*2)
        
        self.observation_space = spaces.MultiBinary(self.num_features)


        #compute action bounds
        lba = 0.0
        uba = float(self.num_features)-1.0
        #-----------------should be changed------------
        self.action_space = spaces.Box(low=lba,
                                        high=uba, shape=(1,), dtype=np.float32)

        #self.action_space = spaces.Discrete(self.num_features)
        #self.seed()
        super().__init__()

    def sample_one(self):
        pos = np.random.randint(low=0, high=self.num_features)
        mask = [0]*self.num_features
        mask[pos]=1
        mask = np.array(mask, dtype=np.int8)
        s = self.observation_space.sample(mask = mask)
        s[pos] = 1
        return s

    def reset(self):
        #reset all values
        self.current_step=1
        #print("reseting")
        self.state = self.sample_one()
        return self.state
        
    
    def step(self,action):
        reward = self._take_action(action)
        self.current_step += 1
        done = False if self.current_step < self._max_episode_steps else True
        obs = self._next_observation()
        return obs, reward, done, {}
    def _take_action(self,action):
        #print("taking action")
        #action is vector of all parameters 
        #call system function to apply changes to the containers etc. and return metrics
        reward = -1.0
        if self.state[int(np.round(action)[0])] == 1: 
            reward = 0.0
            self.state = self.sample_one()
        return reward
        
    def _next_observation(self):
        #print("next observation")
        return self.state
        ##call to system function -- return vector in the order 2*Microservices features + 2 node level features + other features


    