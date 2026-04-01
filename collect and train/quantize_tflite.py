import tensorflow as tf

# Load the trained model
model = tf.keras.models.load_model("lora_spectrum_model.h5")

# Convert to TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Apply Float 16 Quantization (As specified in the PDF)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]

tflite_model = converter.convert()

# Save the compressed model
with open("lora_spectrum_model_fp16.tflite", "wb") as f:
    f.write(tflite_model)

print("Float16 Quantized TFLite Model saved successfully.")