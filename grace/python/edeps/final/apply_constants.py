import gondola as go
import csv
import pandas as pd
import matplotlib.pyplot as plt
import uproot
import numpy as np

'''

Hi Achim! I am writing this script just showing how to apply my energy deposition constants. 
I hope this is helpful and not a waste of your time to read (:

PS: Jump to line 121 to skip the initialization steps!! 

🐍💪

'''

## initializing the paddle id --> volume id map (input = paddle id; output = vol id)
tof_map, trkr_map = go.db.get_hid_vid_maps()

# ============================================================
# Getting everything ready...
# ============================================================
## the calibration constants are stored in a .csv file: 
calibration_constants = {}

with open("/home/gtytus/analysis/grace/python/edeps/final/paddle_calibrations.csv", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        paddle = int(row["paddle"])
        
        ## the slope, y_intercept and T_avg are used for the intra-paddle temperature calibration, 
        ## and the normalization_coeff is used for the inter-paddle MIP MPV calibration.
        calibration_constants[paddle] = {
            "slope": float(row["slope"]),
            "y_intercept": float(row["y_intercept"]),
            "T_avg": float(row["T_avg"]),
            "coefficient": float(row["normalization_coeff"]),
        }

## temperature data is stored as .h5 binary file, which natively opens with pandas (sorry)
## this is also obviously not how you'd open this !! 

sipm_temps = pd.read_hdf('/home/gtytus/analysis/grace/python/sipm_temps/sipm_temps.h5')

# the timestamps reported from the PAMoniData are in MET, and so I calibrate them to their t0:
start_unix_pa = 1765793920
sipm_temps["timestamp_cal"] = start_unix_pa + sipm_temps["timestamp"].astype('int64')
sipm_temps = sipm_temps.sort_values("timestamp_cal")

# I only consider timestamps beyond 251220 since I am calibrating them to energy depositions which only stabilized after gain adjustements on 251219
cutoff = 1766188800
sipm_temps = sipm_temps[sipm_temps['timestamp_cal'] > cutoff]

# since the PAMoniData reports temps per SiPM, I have to collate the temperatures in time and average over each paddle. this is an approximation. 
sipm_temps["paddle_num"] = sipm_temps["paddle"].str[:-1].astype(int)
sipm_temps["side"] = sipm_temps["paddle"].str[-1]
db_paddle_temps = (
    sipm_temps.groupby(["paddle_num", "timestamp_cal"])["temp"]
      .mean()
      .reset_index()
)


## dEdx is stored in a .root file. this is obviously not what you'll do, but it is how I did this calibration
## I used pandas here (sorry) because it makes the merging easier, but I hope it is not too inconvenient. 
f = uproot.open("/data/gtytus/track_edep.root")
tree = f["tracks"]

db_edeps = tree.arrays(
    ["edep", "step_length", "volume_id", "timestamp"],
    library="pd"
).astype({"timestamp": "int64"})

# Only consider data after gain corrections stabilized:
db_edeps = db_edeps[db_edeps["timestamp"] > cutoff]

# Normalize by path length [MeV/cm]: 
db_edeps["dedx"] = db_edeps["edep"] / db_edeps["step_length"]

'''

Now that everything has been initialized, we can actually start the example! 
Of course, we will use paddle 42 (:

Otherwise, this is where the loop would begin! 

'''
# ============================================================
# Step -1: Merging the data
# ============================================================
# We will need to assign temperatures to hits based on a fixed window, as hits occur much more frequently than temperature readings
# (this is a mild benefit of using pandas)
# The maximum tolerance is 30seconds, but because we have chosen direction="nearest", it is likely usually much closer
#
# If you just similarly group and store the temperature in every event, that would certainly be faster!
paddle_num = 68
paddle_temps = db_paddle_temps[db_paddle_temps["paddle_num"] == paddle_num]
paddle_edeps = db_edeps[db_edeps["volume_id"] == tof_map[paddle_num]]

paddle_merged_db = pd.merge_asof(
    paddle_edeps.sort_values("timestamp"),
    paddle_temps.sort_values("timestamp_cal"),
    left_on="timestamp",
    right_on="timestamp_cal",
    direction="nearest",
    tolerance=30
)

paddle_merged_db = paddle_merged_db.dropna(subset=["temp", "dedx"])
paddle_merged_db = paddle_merged_db[paddle_merged_db['edep']> 0.0001] # needed to remove noise! 

# this is the fully uncalibrated dEdx:
dedx_uncorrected = paddle_merged_db["dedx"]

# this is the temperature information:
temperatures_paddle = paddle_merged_db["temp"]

# ============================================================
# Temperature Calibration
# ============================================================
## we need to apply the slope and y_intercept to each temperature value, to get a predicted MPV from the fit: 
slope        = calibration_constants[paddle_num]["slope"]
y_int        = calibration_constants[paddle_num]["y_intercept"]
t_avg        = calibration_constants[paddle_num]["T_avg"]

mpv_predicted  = temperatures_paddle*slope + y_int
mpv_reference  = t_avg*slope + y_int

# temperature calibration formula:
dedx_corrected = dedx_uncorrected*(mpv_reference/mpv_predicted)

# ============================================================
# MIP MPV Normalization
# ============================================================

normalization_coeff = calibration_constants[paddle_num]["coefficient"]
dedx_normalized = dedx_corrected*normalization_coeff

# ============================================================
# Validation Plot
# ============================================================
plt.figure(figsize=(9, 5))
plt.hist(
        dedx_uncorrected,
        bins=1000,
        range=(0, 35),
        histtype="step",
        color="mediumblue",
        label="uncorrected"
    )

plt.hist(
        dedx_corrected, 
        bins=1000,
        range=(0, 35),
        histtype="step",
        color="tomato",
        label="temperature corrected"
    )

plt.hist(
        dedx_normalized,
        bins=1000,
        range=(0, 35),
        histtype="step",
        color="black",
        label="corrected temperature + MIP normalized"
    )

plt.axvline(1.92, linestyle="--",label="Z=1 MPV = 1.92 MeV/cm")
plt.axvline(8.064, linestyle="--",label="Z=2 MPV = 8.064 MeV/cm")
plt.xlabel("dE/dx [MeV/cm]")
plt.ylabel("Counts")
plt.title(f'dE/dx paddle {paddle_num}')
plt.xlim(0, 20)
plt.yscale("log")
plt.legend()
plt.tight_layout()
plt.savefig(f"dEdx_paddle_{paddle_num}.png", dpi=150)
plt.close()






