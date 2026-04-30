import pandas as pd
import csv

df = pd.read_csv("channel_to_paddle.csv")

# Create channel -> paddle mapping, with padded paddle numbers
channel_to_paddle = {
    f"{row['pb_number_channel']}": f"{int(row['paddle_number']):02d}{row['paddle_end']}"
    for _, row in df.iterrows()
}

# Optional: create empty dictionary for paddle temperatures
paddle_temps = {f"{i}{end}": [] for i in range(1,161) for end in ["A","B"]}

# Write mapping to CSV
with open('mapping.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=channel_to_paddle.keys())
    writer.writeheader()
    writer.writerow(channel_to_paddle)

print(paddle_temps)
