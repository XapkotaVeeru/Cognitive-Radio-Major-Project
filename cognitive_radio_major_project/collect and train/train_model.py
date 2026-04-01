import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split

print("Loading dataset...")
data = np.load("real_lora_dataset.npz")
X = data['X']
y = data['y']

X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

# Build the exact model from the PDF (Section 7.2.2)
model = tf.keras.Sequential([
    tf.keras.layers.InputLayer(input_shape=(1024, 2)),
    tf.keras.layers.Reshape((1024, 2, 1)),
    
    tf.keras.layers.ZeroPadding2D(padding=((1, 1), (0, 0))),
    tf.keras.layers.Conv2D(32, kernel_size=(3, 2), activation='relu', padding='valid'),
    tf.keras.layers.Conv2D(32, kernel_size=(3, 2), activation='relu', padding='same'),
    
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation='relu'),
    
    # 4 Output classes representing [00, 01, 10, 11]
    tf.keras.layers.Dense(4, activation='softmax')
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.summary()

# Train (15 Epochs as stated in PDF)
model.fit(X_train, y_train, epochs=15, validation_data=(X_val, y_val), batch_size=32)

loss, acc = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {acc*100:.2f}%")
model.save("lora_spectrum_model_2ch.h5")

# --- Export to TFLite Float16 ---
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types =[tf.float16]
tflite_model = converter.convert()

with open("lora_model_fp16.tflite", "wb") as f:
    f.write(tflite_model)
print("Float16 TFLite Model Saved!")