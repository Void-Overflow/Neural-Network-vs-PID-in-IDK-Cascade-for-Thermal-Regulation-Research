# Neural-Network-vs-PID-in-IDK-Cascade-for-Thermal-Regulation-Research

This research study presents a Python-based embedded system for real-time thermal regulation of a Peltier element using an IDK-Cascade control strategy. The system is designed to dynamically switch between multiple neural networks (NNs) and a traditional PID controller based on varying confidence intervals.

Two neural networks are employed in the cascade:

- **NN1 (Fast):** A lightweight, reactive network designed to make rapid duty cycle predictions, favoring speed and responsiveness over stability.
- **NN2 (Slow):** A deeper, more conservative network optimized for smoother temperature regulation and reduced power draw, at the cost of slightly higher computational overhead.

- **PID Controller:** Serves as a fallback deterministic stage when both NNs fall below confidence thresholds or when highly stable behavior is needed.

Both networks are trained on datasets collected from PID-controlled thermal regulation and deployed using TensorFlow Lite Micro on a Raspberry Pi Zero W (ARMv6l architecture). The IDK-Cascade dynamically routes control between NN1, NN2, and PID depending on their confidence scores, balancing latency, stability, and power efficiency.

This work is part of a research study and paper conducted at the University of Houston’s Real-Time Systems Laboratory under the guidance of Professor Albert M. Cheng and Ph.D. student Thomas P. Carroll. It aims to analyze and compare the performance and efficiency of IDK-Cascade control in embedded environments across multiple confidence levels based on factors like power consumption, latency, and standard deviation of the temperature over a set 45 minute duration throughout the trials.

This paper is being submitted to be presented at the Real-Time Systems Symposium (RTSS) Conference in Boston in December 2025 as a WiP research paper. The research paper is available in this GitHub repository as a PDF as well.
- `publication/Work_in_Progress__Evaluating_Stage_Prioritized_IDK_Cascades_for_Thermal_Regulation_in_Embedded_Systems.pdf`: PDF document of research paper conducted over this study which is going to be submitted to RTSS.

## Features

- NN-based thermal controller trained from PID data and deployed via TFLite-Micro
- IDK-Cascade switching between NN and PID based on confidence thresholds (30%, 50%, 70%)
- Real-time control of Peltier element via PWM on Raspberry Pi Zero W
- Support for hardware-level data logging including:
  - Temperature
  - Duty cycle
  - Latency
  - Power draw
- CSV logging for further training and analysis

## Hardware Setup

To enhance reproducibility and transparency, this repository includes detailed hardware documentation:

- `hardware_documentation/schematic/`: Electrical schematic of the system
- `hardware_documentation/images/`: Photographs of the embedded setup
- `hardware_documentation/operational_video/`: Real-time video demonstration

## Requirements

Due to compatibility limitations of TensorFlow-Lite Micro on Raspberry Pi Zero W, this project uses:

- Python 3.7
- A lightweight virtual environment (`venv`)
- TensorFlow Lite Micro (`tflite-micro-runtime`)
- Adafruit drivers for I²C-based sensors (ADS1115, INA219)

To install all necessary libraries, activate your Python 3.7 environment and run:

``` bash
pip3 install -r requirements.txt
```
# Usage
Run the main application:
```bash
python main.py
```

# License
This project's is licensed under the MIT License, while it's image and video documentation is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.

# Acknowledgments
Developed at the University of Houston Real-Time Systems Lab with
Prof. Albert M. Cheng
Thomas P. Carroll, Ph.D. Student
