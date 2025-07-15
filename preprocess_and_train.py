#preprocess_and_train.py

# This file is used to train the neural network using previously obtained PID research data
# Tensorflow is unable to be run on the Raspberry Pi Zero W due to hardware limitations, so 
# this file can only be run on an external computer in order to generate the necessary
# TFLite files which can then be successfully run and interpreted on the RPI Zero W.

import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("research_data/PID/raw_data.csv")

df.columns = df.columns.str.strip()

X = df[["Temperature (C)", "Latency (ms)", "Power (W)"]]  # Inputs
y = df["Duty Cycle (%)"]                                  # Output 

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

model = Sequential([
    Dense(32, activation='relu', input_shape=(X.shape[1],)),
    Dense(16, activation='relu'),
    Dense(1) 
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])

model.fit(X_train, y_train, epochs=50, validation_data=(X_test, y_test))

model.save("neural_network/thermal_controller_model.h5")
np.save("neural_network/scaler_mean.npy", scaler.mean_)
np.save("neural_network/scaler_scale.npy", scaler.scale_)
