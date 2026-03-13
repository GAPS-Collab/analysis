import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

plt.figure(figsize=(10,3))
df = pd.read_hdf("sipm_temps.h5")
df["temp"] = df["temp"].clip(upper=30) 
sns.lineplot(data=df, x="timestamp", y="temp", hue="paddle", legend=False, errorbar=None)
plt.xlabel("Time")
plt.ylabel("Temperature [°C]")
plt.savefig('all_temp.png')
