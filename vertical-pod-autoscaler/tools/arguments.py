import argparse


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--approach", help="The optimization algorithm to be used", default="PBR")
    parser.add_argument(
        "--control_plane", help="The IP of the kubernetes control plane", default="localhost")
    parser.add_argument("--experiment_version", "-v", "-V",
                        help="The version of the experiment")
    parser.add_argument("--experiment_folder", "-ef",
                        help="The root folder where all the results are stored.", default="/home/ubuntu/autoscaler/vertical-pod-autoscaler/experiments")
    parser.add_argument("--experiment_iterations", "-ei",
                        help="The number of times the experiment is repeated for a given algorithm and config (0th iteration is run for cache warm-up", default=1, type=int)
    parser.add_argument("--model_iterations", "-mi",
                        help="The number of iterations the algorithm is run in each sequence", default=12, type=int)
    parser.add_argument("--experiment_type", "-et",
                        help="The type of experiment - {nginx, redis, DeathStarBenchmark}", default="nginx")
    parser.add_argument("--workload_type", "-wt",
                        help="The type of workload - {bursty, diurnal, random, etc}", default="random")
    parser.add_argument("--sequence_count", "-sc",
                        help="The number of times the algorithm is rerun", default=1, type=int)
    parser.add_argument("--start_sequence", "-ss",
                        help="Starting sequence number", default=1, type=int)
    parser.add_argument("--experiment_duration", "-ed",
                        help="The duration of the online experiment in minutes", default="3600")
    parser.add_argument("--test", action="store_true",
                        help="Temporary flags that is used to test a feature conditionally.")
    parser.add_argument("--online", action="store_true",
                        help="If passed, the experiment is run online")
    parser.add_argument("--monitoring_interval",
                        help="The interval at which the config is changed", default="3")
    parser.add_argument("--init", action="store_true",
                        help="Initialize the algorithm with user supplied points instead of library generated random samples.")
    return parser.parse_args()
