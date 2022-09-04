import ContainerizedEnv
import sys

if __name__ == "__main__":
    args1 = 1
    args2 = 2
    env = ContainerizedEnv.ContainerEnv(sys.argv[1])
    env.reset()
    action = env.action_space.sample()
    obs, reward,_,_ =  env.step(action, args1, args2)
    print(obs)
    print(reward)
