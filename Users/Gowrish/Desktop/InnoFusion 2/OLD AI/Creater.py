#!/usr/bin/env python3
"""
Enhanced LSTM with Classification Head for Predictive Maintenance
Features:
- Real-time pattern analysis
- Future health prediction with time estimates
- Failure prediction and maintenance scheduling
- Parameter-specific failure analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    LSTM, Dense, Dropout, Input, Conv1D, GlobalMaxPooling1D,
    Concatenate, BatchNormalization, Attention, MultiHeadAttention, Lambda
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import pickle
import warnings
warnings.filterwarnings('ignore')

class PredictiveMaintenanceLSTM:
    """
    Enhanced LSTM model for predictive maintenance with failure time estimation
    """
    
    def __init__(self, sequence_length=15, prediction_horizon=5):
        self.sequence_length = sequence_length  # Look-back window
        self.prediction_horizon = prediction_horizon  # Predict 5 steps ahead
        self.scaler = StandardScaler()
        self.model = None
        self.feature_names = [
            'Temperature', 'Humidity', 'Air_Flow_Rate', 
            'Fan_Speed', 'Heating_Power', 'Fan_Power'
        ]
        
        # Parameter failure thresholds and degradation patterns
        self.failure_patterns = {
            'Temperature': {
                'critical_low': 20.0, 'critical_high': 35.0,
                'warning_low': 22.0, 'warning_high': 32.0,
                'optimal_low': 26.0, 'optimal_high': 30.0,
                'degradation_rate': 0.1  # per hour
            },
            'Humidity': {
                'critical_low': 40.0, 'critical_high': 80.0,
                'warning_low': 45.0, 'warning_high': 75.0,
                'optimal_low': 60.0, 'optimal_high': 70.0,
                'degradation_rate': 0.5
            },
            'Air_Flow_Rate': {
                'critical_low': 80.0, 'critical_high': 150.0,
                'warning_low': 90.0, 'warning_high': 140.0,
                'optimal_low': 110.0, 'optimal_high': 130.0,
                'degradation_rate': 0.2
            },
            'Fan_Speed': {
                'critical_low': 1800, 'critical_high': 2400,
                'warning_low': 1900, 'warning_high': 2350,
                'optimal_low': 2100, 'optimal_high': 2300,
                'degradation_rate': 5.0
            },
            'Heating_Power': {
                'critical_low': 12.0, 'critical_high': 18.0,
                'warning_low': 13.0, 'warning_high': 17.0,
                'optimal_low': 14.0, 'optimal_high': 16.0,
                'degradation_rate': 0.05
            },
            'Fan_Power': {
                'critical_low': 180.0, 'critical_high': 270.0,
                'warning_low': 190.0, 'warning_high': 260.0,
                'optimal_low': 210.0, 'optimal_high': 240.0,
                'degradation_rate': 0.1
            }
        }
    
    def generate_enhanced_dataset(self, num_samples=5000):
        """
        Generate enhanced dataset with temporal patterns and failure scenarios
        """
        print("🔧 Generating enhanced dataset with failure patterns...")
        
        data = []
        labels = []
        failure_indicators = []
        time_to_failure = []
        
        for i in range(num_samples):
            # Generate base operating conditions
            if i < num_samples * 0.6:  # 60% healthy
                health_status = 0  # Healthy
                temp_base = np.random.normal(28, 1)
                hum_base = np.random.normal(65, 3)
                air_base = np.random.normal(120, 5)
                fan_speed_base = np.random.normal(2200, 50)
                heat_base = np.random.normal(15, 0.5)
                power_base = np.random.normal(225, 5)
                ttf = np.random.uniform(100, 200)  # Hours to potential failure
                
            elif i < num_samples * 0.85:  # 25% warning
                health_status = 1  # Warning
                temp_base = np.random.choice([
                    np.random.normal(24, 1),  # Too low
                    np.random.normal(32, 1)   # Too high
                ])
                hum_base = np.random.choice([
                    np.random.normal(50, 2),  # Too low
                    np.random.normal(75, 2)   # Too high
                ])
                air_base = np.random.choice([
                    np.random.normal(95, 3),   # Too low
                    np.random.normal(135, 3)   # Too high
                ])
                fan_speed_base = np.random.choice([
                    np.random.normal(1950, 30), # Too low
                    np.random.normal(2320, 30)  # Too high
                ])
                heat_base = np.random.choice([
                    np.random.normal(13.2, 0.3), # Too low
                    np.random.normal(16.8, 0.3)  # Too high
                ])
                power_base = np.random.choice([
                    np.random.normal(195, 5), # Too low
                    np.random.normal(255, 5)  # Too high
                ])
                ttf = np.random.uniform(20, 50)  # Hours to potential failure
                
            else:  # 15% critical/failure
                health_status = 2  # Critical
                temp_base = np.random.choice([
                    np.random.normal(19, 0.5),  # Critically low
                    np.random.normal(36, 0.5)   # Critically high
                ])
                hum_base = np.random.choice([
                    np.random.normal(35, 2),    # Critically low
                    np.random.normal(85, 2)     # Critically high
                ])
                air_base = np.random.choice([
                    np.random.normal(75, 2),    # Critically low
                    np.random.normal(155, 2)    # Critically high
                ])
                fan_speed_base = np.random.choice([
                    np.random.normal(1750, 20), # Critically low
                    np.random.normal(2450, 20)  # Critically high
                ])
                heat_base = np.random.choice([
                    np.random.normal(11.5, 0.2), # Critically low
                    np.random.normal(18.5, 0.2)  # Critically high
                ])
                power_base = np.random.choice([
                    np.random.normal(175, 5),  # Critically low
                    np.random.normal(275, 5)  # Critically high
                ])
                ttf = np.random.uniform(1, 10)  # Hours to failure
            
            # Add temporal patterns and noise
            sequence = []
            for t in range(self.sequence_length):
                # Add time-based variations
                time_factor = np.sin(t * 0.1) * 0.1
                noise_factor = np.random.normal(0, 0.05)
                
                temp = temp_base + time_factor * 2 + noise_factor
                hum = hum_base + time_factor * 3 + noise_factor * 2
                air = air_base + time_factor * 5 + noise_factor * 3
                fan_speed = fan_speed_base + time_factor * 20 + noise_factor * 10
                heat = heat_base + time_factor * 0.5 + noise_factor * 0.2
                power = power_base + time_factor * 0.5 + noise_factor * 0.2
                
                # Add degradation trends for warning/critical states
                if health_status > 0:
                    degradation = t * 0.02 * health_status
                    temp += degradation * np.random.choice([-1, 1])
                    hum += degradation * np.random.choice([-1, 1]) * 2
                    air += degradation * np.random.choice([-1, 1]) * 3
                    fan_speed += degradation * np.random.choice([-1, 1]) * 15
                
                sequence.append([temp, hum, air, fan_speed, heat, power])
            
            data.append(sequence)
            labels.append(health_status)
            
            # Failure indicators (binary for each parameter)
            failure_indicator = []
            current_values = sequence[-1]  # Latest values
            
            for j, param_name in enumerate(self.feature_names):
                pattern = self.failure_patterns[param_name]
                value = current_values[j]
                
                # Check if parameter is in failure range
                if (value <= pattern['critical_low'] or 
                    value >= pattern['critical_high']):
                    failure_indicator.append(1)
                else:
                    failure_indicator.append(0)
            
            failure_indicators.append(failure_indicator)
            time_to_failure.append(ttf)
        
        # Convert to numpy arrays
        X = np.array(data)
        y = np.array(labels)
        failure_indicators = np.array(failure_indicators)
        time_to_failure = np.array(time_to_failure)
        
        print(f"✅ Generated dataset shape: X={X.shape}, y={y.shape}")
        print(f"   Healthy: {np.sum(y == 0)} samples")
        print(f"   Warning: {np.sum(y == 1)} samples") 
        print(f"   Critical: {np.sum(y == 2)} samples")
        
        return X, y, failure_indicators, time_to_failure
    
    def build_enhanced_model(self, input_shape):
        """
        Build enhanced LSTM model with classification head and failure prediction
        """
        print("🏗️ Building enhanced LSTM model with classification head...")
        
        # Input layer
        inputs = Input(shape=input_shape, name='sensor_input')
        
        # LSTM branch for temporal patterns
        lstm1 = LSTM(128, return_sequences=True, dropout=0.2, name='lstm_1')(inputs)
        lstm1 = BatchNormalization(name='bn_lstm1')(lstm1)
        
        lstm2 = LSTM(64, return_sequences=True, dropout=0.2, name='lstm_2')(lstm1)
        lstm2 = BatchNormalization(name='bn_lstm2')(lstm2)
        
        lstm3 = LSTM(32, return_sequences=False, dropout=0.2, name='lstm_3')(lstm2)
        
        # CNN branch for feature extraction
        conv1 = Conv1D(64, 3, activation='relu', name='conv_1')(inputs)
        conv1 = BatchNormalization(name='bn_conv1')(conv1)
        conv1 = Dropout(0.2)(conv1)
        
        conv2 = Conv1D(32, 3, activation='relu', name='conv_2')(conv1)
        conv2 = BatchNormalization(name='bn_conv2')(conv2)
        conv2 = GlobalMaxPooling1D(name='global_pool')(conv2)
        
        # Statistical features branch
        stats_mean = Lambda(lambda x: tf.reduce_mean(x, axis=1))(inputs)
        stats_std = Lambda(lambda x: tf.math.reduce_std(x, axis=1))(inputs)
        stats_max = Lambda(lambda x: tf.reduce_max(x, axis=1))(inputs)
        stats_min = Lambda(lambda x: tf.reduce_min(x, axis=1))(inputs)
        
        stats_features = Concatenate(name='stats_concat')([
            stats_mean, stats_std, stats_max, stats_min
        ])
        stats_dense = Dense(16, activation='relu', name='stats_dense')(stats_features)
        
        # Combine all branches
        combined = Concatenate(name='feature_fusion')([lstm3, conv2, stats_dense])
        combined = Dense(128, activation='relu', name='fusion_dense1')(combined)
        combined = BatchNormalization(name='bn_fusion')(combined)
        combined = Dropout(0.3)(combined)
        
        combined = Dense(64, activation='relu', name='fusion_dense2')(combined)
        combined = Dropout(0.2)(combined)
        
        # Classification head for health status
        health_output = Dense(32, activation='relu', name='health_dense')(combined)
        health_output = Dense(3, activation='softmax', name='health_classification')(health_output)
        
        # Failure prediction head (binary for each parameter)
        failure_output = Dense(32, activation='relu', name='failure_dense')(combined)
        failure_output = Dense(6, activation='sigmoid', name='failure_prediction')(failure_output)
        
        # Time to failure regression head
        ttf_output = Dense(32, activation='relu', name='ttf_dense')(combined)
        ttf_output = Dense(1, activation='linear', name='time_to_failure')(ttf_output)
        
        # Create model
        model = Model(
            inputs=inputs, 
            outputs={
                'health_classification': health_output,
                'failure_prediction': failure_output,
                'time_to_failure': ttf_output
            }
        )
        
        # Compile with multiple losses
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss={
                'health_classification': 'sparse_categorical_crossentropy',
                'failure_prediction': 'binary_crossentropy',
                'time_to_failure': 'mse'
            },
            loss_weights={
                'health_classification': 1.0,
                'failure_prediction': 0.5,
                'time_to_failure': 0.3
            },
            metrics={
                'health_classification': ['accuracy'],
                'failure_prediction': ['binary_accuracy'],
                'time_to_failure': ['mae']
            }
        )
        
        return model
    
    def train_model(self, X, y, failure_indicators, time_to_failure):
        """
        Train the enhanced model
        """
        print("🚀 Training enhanced LSTM model...")
        
        # Reshape data for LSTM
        X_reshaped = X.reshape(X.shape[0], X.shape[1], X.shape[2])
        
        # Scale the features
        X_scaled = np.zeros_like(X_reshaped)
        for i in range(X_reshaped.shape[0]):
            X_scaled[i] = self.scaler.fit_transform(X_reshaped[i])
        
        # Split data
        X_train, X_test, y_train, y_test, failure_train, failure_test, ttf_train, ttf_test = train_test_split(
            X_scaled, y, failure_indicators, time_to_failure, 
            test_size=0.2, random_state=42, stratify=y
        )
        
        # Build model
        self.model = self.build_enhanced_model((X_train.shape[1], X_train.shape[2]))
        
        print("📊 Model architecture:")
        self.model.summary()
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6),
            ModelCheckpoint('enhanced_lstm_model.h5', save_best_only=True, monitor='val_loss')
        ]
        
        # Train model
        history = self.model.fit(
            X_train,
            {
                'health_classification': y_train,
                'failure_prediction': failure_train,
                'time_to_failure': ttf_train
            },
            validation_data=(
                X_test,
                {
                    'health_classification': y_test,
                    'failure_prediction': failure_test,
                    'time_to_failure': ttf_test
                }
            ),
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate model
        print("\n📈 Evaluating model performance...")
        test_results = self.model.evaluate(
            X_test,
            {
                'health_classification': y_test,
                'failure_prediction': failure_test,
                'time_to_failure': ttf_test
            },
            verbose=0
        )
        
        print(f"✅ Test Results:")
        print(f"   Overall Loss: {test_results[0]:.4f}")
        print(f"   Health Classification Accuracy: {test_results[4]:.4f}")
        print(f"   Failure Prediction Accuracy: {test_results[5]:.4f}")
        print(f"   Time to Failure MAE: {test_results[6]:.2f} hours")
        
        # Detailed classification report
        y_pred = self.model.predict(X_test, verbose=0)
        health_pred = np.argmax(y_pred['health_classification'], axis=1)
        
        print("\n📋 Detailed Classification Report:")
        print(classification_report(y_test, health_pred, 
                                  target_names=['Healthy', 'Warning', 'Critical']))
        
        # Save model and scaler
        self.model.save('enhanced_lstm_health_model.h5')
        with open('enhanced_scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print("💾 Model and scaler saved successfully!")
        
        # Plot training history
        self.plot_training_history(history)
        
        return history
    
    def plot_training_history(self, history):
        """
        Plot training history
        """
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('Enhanced LSTM Training History', fontsize=16, fontweight='bold')
        
        # Health classification accuracy
        axes[0, 0].plot(history.history['health_classification_accuracy'], label='Train')
        axes[0, 0].plot(history.history['val_health_classification_accuracy'], label='Val')
        axes[0, 0].set_title('Health Classification Accuracy')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Accuracy')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Health classification loss
        axes[0, 1].plot(history.history['health_classification_loss'], label='Train')
        axes[0, 1].plot(history.history['val_health_classification_loss'], label='Val')
        axes[0, 1].set_title('Health Classification Loss')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('Loss')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # Failure prediction accuracy
        axes[0, 2].plot(history.history['failure_prediction_binary_accuracy'], label='Train')
        axes[0, 2].plot(history.history['val_failure_prediction_binary_accuracy'], label='Val')
        axes[0, 2].set_title('Failure Prediction Accuracy')
        axes[0, 2].set_xlabel('Epoch')
        axes[0, 2].set_ylabel('Accuracy')
        axes[0, 2].legend()
        axes[0, 2].grid(True)
        
        # Failure prediction loss
        axes[1, 0].plot(history.history['failure_prediction_loss'], label='Train')
        axes[1, 0].plot(history.history['val_failure_prediction_loss'], label='Val')
        axes[1, 0].set_title('Failure Prediction Loss')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('Loss')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Time to failure MAE
        axes[1, 1].plot(history.history['time_to_failure_mae'], label='Train')
        axes[1, 1].plot(history.history['val_time_to_failure_mae'], label='Val')
        axes[1, 1].set_title('Time to Failure MAE')
        axes[1, 1].set_xlabel('Epoch')
        axes[1, 1].set_ylabel('MAE (hours)')
        axes[1, 1].legend()
        axes[1, 1].grid(True)
        
        # Overall loss
        axes[1, 2].plot(history.history['loss'], label='Train')
        axes[1, 2].plot(history.history['val_loss'], label='Val')
        axes[1, 2].set_title('Overall Loss')
        axes[1, 2].set_xlabel('Epoch')
        axes[1, 2].set_ylabel('Loss')
        axes[1, 2].legend()
        axes[1, 2].grid(True)
        
        plt.tight_layout()
        plt.savefig('enhanced_lstm_training_history.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("📊 Training plots saved as 'enhanced_lstm_training_history.png'")

def main():
    """
    Main training function
    """
    print("🚀 ENHANCED LSTM WITH PREDICTIVE MAINTENANCE TRAINING")
    print("=" * 60)
    
    # Initialize model
    pm_lstm = PredictiveMaintenanceLSTM(sequence_length=15, prediction_horizon=5)
    
    # Generate enhanced dataset
    X, y, failure_indicators, time_to_failure = pm_lstm.generate_enhanced_dataset(num_samples=5000)
    
    # Train model
    history = pm_lstm.train_model(X, y, failure_indicators, time_to_failure)
    
    print("\n✅ TRAINING COMPLETED SUCCESSFULLY!")
    print("📁 Files created:")
    print("   - enhanced_lstm_health_model.h5")
    print("   - enhanced_scaler.pkl")
    print("   - enhanced_lstm_training_history.png")
    
    print("\n🎯 Next steps:")
    print("   Run the enhanced real-time monitor for predictive maintenance!")

if __name__ == "__main__":
    main()
