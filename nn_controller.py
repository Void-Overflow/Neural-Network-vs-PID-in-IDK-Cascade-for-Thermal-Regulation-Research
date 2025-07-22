# nn_controller.py
import tflite_micro_runtime.interpreter as tflite
import numpy as np

class NeuralNetController:
    def __init__(self, model_path, model_name="thermal_controller_model.tflite"):
        self.model_path = model_path
        
        self.interpreter = tflite.Interpreter(model_path=self.model_path + model_name)
        self.interpreter.allocate_tensors()
        self.output_details = self.interpreter.get_output_details()
        self.input_details = self.interpreter.get_input_details()
        

        self.mean = np.load(self.model_path + "scaler_mean.npy")
        self.scale = np.load(self.model_path + "scaler_scale.npy")

    def predict(self, temperature, power, latency):
        raw_input = np.array([temperature, latency, power])
        scaled_input = (raw_input - self.mean) / self.scale
        input_data = np.array([scaled_input], dtype=np.float32)

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        return max(0, min(100, float(output_data[0][0])))  # Output: duty cycle (0–100)
