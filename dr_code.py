# -*- coding: utf-8 -*-
"""DR_code.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1JURlyYzeZ-xlyBCr6iyksj9WhBg7RTsO
"""

pip install tensorflow scikit-learn streamlit opencv-python-headless pillow

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn import svm
from sklearn.preprocessing import StandardScaler
import joblib # Import joblib directly instead of from sklearn.externals

from google.colab import drive
drive.mount("/content/drive")

import os

# Path to the main directory containing your folders
main_folder_path = '/content/drive/MyDrive/Dataset2'

# List all folders in the main directory
folders = [f for f in os.listdir(main_folder_path) if os.path.isdir(os.path.join(main_folder_path, f))]
print(folders)  # This will print the names of your folders

import os

# Path to your main directory in Google Drive
path_data = '/content/drive/MyDrive/Dataset2'  # Update this path

# List the main folder contents
data = os.listdir(path_data)

# List each category folder's contents
healthy = os.listdir(os.path.join(path_data, 'Healthy'))
mild = os.listdir(os.path.join(path_data, 'Mild DR'))
moderate = os.listdir(os.path.join(path_data, 'Moderate DR'))
proliferate = os.listdir(os.path.join(path_data, 'Proliferate DR'))
severe = os.listdir(os.path.join(path_data, 'Severe DR'))

# Optional: Print the contents for verification
print("Healthy images:", healthy)
print("Mild DR images:", mild)
print("Moderate DR images:", moderate)
print("Proliferate DR images:", proliferate)
print("Severe DR images:", severe)

print("classes names :", (data), "\n______________________________\n")
print("Number of classes :", len(data), "\n______________________________\n")
print("Number of Healty images :", len(healthy), "\n______________________________\n")
print("Number of Mild images :", len(mild),  "\n______________________________\n")
print("Number of Moderate images :", len(moderate),  "\n______________________________\n")
print("Number of Proliferate images :", len(proliferate),  "\n______________________________\n")
print("Number of severe images :", len(severe),  "\n______________________________\n")

main_folder_path = '/content/drive/MyDrive/Dataset2'
IMG_SIZE = (128, 128)
BATCH_SIZE = 32

datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2,
    horizontal_flip=True,
    rotation_range=20,
    zoom_range=0.2,
)

# Load data
train_data_gen = datagen.flow_from_directory(
    main_folder_path,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training'
)

val_data_gen = datagen.flow_from_directory(
    main_folder_path,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation'
)
print("Class labels:", train_data_gen.class_indices)

from tensorflow.keras import layers, models

def create_cnn(input_shape=(128, 128, 3), num_classes=5):
    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(num_classes, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

# Train CNN Model
cnn_model = create_cnn()
cnn_model.fit(train_data_gen, validation_data=val_data_gen, epochs=10)
cnn_model.save('cnn_model.h5')

# Extract features for SVM training
X_train_features = []
y_train_labels = []

for images, labels in train_data_gen:
    features = cnn_model.predict(images)
    X_train_features.extend(features)
    y_train_labels.extend(labels)
    if len(X_train_features) >= train_data_gen.samples:
        break

# Train SVM
svm_model = svm.SVC(kernel='linear', probability=True)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_features)
svm_model.fit(X_train_scaled, np.argmax(y_train_labels, axis=1))

# Save SVM and scaler
joblib.dump(svm_model, 'svm_model.pkl')
joblib.dump(scaler, 'scaler.pkl')

def ensemble_predict(image, cnn_model, svm_model, scaler):
    cnn_pred = cnn_model.predict(image)[0]
    cnn_class = np.argmax(cnn_pred)

    # Flatten and scale image for SVM
    image_flatten = image.flatten().reshape(1, -1)
    image_scaled = scaler.transform(image_flatten)
    svm_pred = svm_model.predict_proba(image_scaled)[0]
    svm_class = np.argmax(svm_pred)

    # Combine predictions (majority voting)
    combined_pred = cnn_pred + svm_pred
    final_class = np.argmax(combined_pred)

    classes = ['Healthy', 'Mild DR', 'Moderate DR', 'Proliferate DR', 'Severe DR']
    return classes[final_class]