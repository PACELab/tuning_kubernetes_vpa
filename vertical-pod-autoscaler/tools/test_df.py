import pandas as pd

parameters_df = pd.read_csv("vpa_parameters.csv", index_col="parameter")
for parameter, meta in parameters_df.iterrows():
    print(index)
    print(row["type"])