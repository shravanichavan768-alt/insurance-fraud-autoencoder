
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt
import os

def build_autoencoder(input_dim):
    input_layer = keras.Input(shape=(input_dim,))

    # Encoder
    encoded = layers.Dense(8, activation='relu')(input_layer)
    encoded = layers.Dense(4, activation='relu')(encoded)

    # Bottleneck
    bottleneck = layers.Dense(2, activation='relu')(encoded)

    # Decoder
    decoded = layers.Dense(4, activation='relu')(bottleneck)
    decoded = layers.Dense(8, activation='relu')(decoded)
    output_layer = layers.Dense(input_dim, activation='linear')(decoded)

    autoencoder = keras.Model(inputs=input_layer, outputs=output_layer)
    autoencoder.compile(optimizer='adam', loss='mse')

    print(autoencoder.summary())
    return autoencoder

def train_autoencoder(autoencoder, X_train_legit, epochs=50, batch_size=32):
    history = autoencoder.fit(
        X_train_legit, X_train_legit,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.1,
        shuffle=True,
        verbose=1
    )

    # Plot training loss
    os.makedirs('outputs', exist_ok=True)
    plt.figure(figsize=(10, 4))
    plt.plot(history.history['loss'], label='Training Loss', color='#2ecc71')
    plt.plot(history.history['val_loss'], label='Validation Loss', color='#e74c3c')
    plt.title('Autoencoder Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.legend()
    plt.tight_layout()
    plt.savefig('outputs/training_loss.png', dpi=150)
    plt.close()

    print("Autoencoder trained ")
    return autoencoder, history

def get_reconstruction_error(autoencoder, X):
    X_pred = autoencoder.predict(X)
    errors = np.mean(np.power(X.values - X_pred, 2), axis=1)
    return errors

def save_autoencoder(autoencoder, path='models/autoencoder_model.h5'):
    os.makedirs('models', exist_ok=True)
    autoencoder.save(path)
    print(f"Autoencoder saved to {path} ")

def load_autoencoder(path='models/autoencoder_model.h5'):
    autoencoder = keras.models.load_model(path)
    print(f"Autoencoder loaded from {path} ")
    return autoencoder

if __name__ == "__main__":
    print("Autoencoder module ready ")