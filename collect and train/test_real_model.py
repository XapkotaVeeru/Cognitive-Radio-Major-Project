import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

print("=== COGNITIVE RADIO AI EVALUATION ===")

# 1. Load the Real Dataset
print("Loading real-world dataset...")
try:
    data = np.load("real_lora_dataset.npz")
    X = data['X']
    y = data['y']
    print(f"Successfully loaded {X.shape[0]} real radio samples.")
except FileNotFoundError:
    print("Error: 'real_lora_dataset.npz' not found. Did you run the collection script?")
    exit()

# 2. Split the data exactly as we did in training to extract the unseen 10% Test Set
# It is CRITICAL to keep random_state=42 so we get the exact same split
_, X_temp, _, y_temp = train_test_split(X, y, test_size=0.2, random_state=42)
_, X_test, _, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

print(f"Testing on {X_test.shape[0]} unseen real-world samples...\n")

# 3. Load the Trained Model
print("Loading trained CNN model...")
try:
    model = tf.keras.models.load_model("lora_spectrum_model_2ch.h5")
except FileNotFoundError:
    print("Error: 'lora_spectrum_model_2ch.h5' not found. Did you retrain the model?")
    exit()

# 4. Evaluate Accuracy & Loss
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"--- Model Evaluation ---")
print(f"Overall Real-World Test Accuracy: {accuracy * 100:.2f}%")
print(f"Overall Real-World Test Loss: {loss:.4f}\n")

# 5. Generate Predictions
print("Generating predictions...")
y_pred_probs = model.predict(X_test)
y_pred = np.argmax(y_pred_probs, axis=1)

# Class Names for your 865-867 MHz IN865 Band Setup
class_names =[
    'Both Free (00)', 
    '865.3 MHz Occupied (10)', 
    '866.3 MHz Occupied (01)', 
    'Both Occupied (11)'
]

# 6. Print Classification Report (Precision, Recall, F1-Score)
print("--- Classification Report ---")
print(classification_report(y_test, y_pred, target_names=class_names))

# 7. Plot the Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(9, 7))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=class_names, yticklabels=class_names,
            annot_kws={"size": 14}) # Make numbers larger for screenshots

plt.title('Confusion Matrix - Real Hardware Spectrum Sensing', fontsize=14)
plt.ylabel('True Physical State', fontsize=12)
plt.xlabel('AI Predicted State', fontsize=12)
plt.xticks(rotation=25, ha='right')
plt.tight_layout()

# Save the graph so you can use it in your project report/presentation!
plt.savefig("real_confusion_matrix.png", dpi=300)
print("\n✅ Confusion Matrix successfully saved as 'real_confusion_matrix.png'!")

# Show the graph on screen
plt.show()