#!/usr/bin/env python3
"""
Retrain LSTM Model with Correct Parameter Ranges
This script will:
1. Generate training data using the same parameter ranges as the monitor
2. Train a new LSTM model with proper health classification
3. Save the model for integration with the monitor
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try to import TensorFlow
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    print("✅ TensorFlow available for model training")
    TENSORFLOW_AVAILABLE = True
except ImportError:
    print("❌ TensorFlow not available - cannot retrain model")
    TENSORFLOW_AVAILABLE = False
    exit(1)

class ModelRetrainer:
    def __init__(self):
        # Same parameter ranges as the monitor - CRITICAL!
        self.failure_patterns = {
            'Temperature': {
                'critical_low': 20.0, 'critical_high': 35.0,
                'warning_low': 22.0, 'warning_high': 32.0,
                'optimal_low': 26.0, 'optimal_high': 30.0,
            },
            'Humidity': {
                'critical_low': 40.0, 'critical_high': 80.0,
                'warning_low': 45.0, 'warning_high': 75.0,
                'optimal_low': 60.0, 'optimal_high': 70.0,
            },
            'Air_Flow_Rate': {
                'critical_low': 80.0, 'critical_high': 150.0,
                'warning_low': 90.0, 'warning_high': 140.0,
                'optimal_low': 110.0, 'optimal_high': 130.0,
            },
            'Fan_Speed': {
                'critical_low': 1800, 'critical_high': 2400,
                'warning_low': 1900, 'warning_high': 2350,
                'optimal_low': 2100, 'optimal_high': 2300,
            },
            'Heating_Power': {
                'critical_low': 12.0, 'critical_high': 18.0,
                'warning_low': 13.0, 'warning_high': 17.0,
                'optimal_low': 14.0, 'optimal_high': 16.0,
            },
            'Fan_Power': {
                'critical_low': 180.0, 'critical_high': 270.0,
                'warning_low': 190.0, 'warning_high': 260.0,
                'optimal_low': 210.0, 'optimal_high': 240.0,
            }
        }
        
        self.param_names = list(self.failure_patterns.keys())
        self.sequence_length = 15
        self.scaler = StandardScaler()
        
    def classify_health_status(self, values):
        """
        Classify health status using SAME logic as monitor
        Returns: 0=HEALTHY, 1=WARNING, 2=CRITICAL
        """
        critical_params = 0
        warning_params = 0
        
        for i, value in enumerate(values):
            param_name = self.param_names[i]
            pattern = self.failure_patterns[param_name]
            
            if value < pattern['critical_low'] or value > pattern['critical_high']:
                critical_params += 1
            elif not (pattern['optimal_low'] <= value <= pattern['optimal_high']):
                # Not in optimal range, check if in warning range
                if (pattern['warning_low'] <= value < pattern['optimal_low']) or (pattern['optimal_high'] < value <= pattern['warning_high']):
                    warning_params += 1
        
        # Same logic as monitor
        if critical_params > 0:
            return 2  # CRITICAL
        elif warning_params > 0:
            return 1  # WARNING
        else:
            return 0  # HEALTHY
    
    def generate_training_data(self, num_samples=10000):
        """Generate training data with realistic parameter distributions"""
        print(f"🔄 Generating {num_samples} training samples...")
        
        sequences = []
        labels = []
        
        for _ in range(num_samples):
            # Generate a sequence of 15 data points
            sequence = []
            
            # Randomly choose a health scenario
            scenario = np.random.choice(['healthy', 'warning', 'critical'], p=[0.6, 0.3, 0.1])
            
            for step in range(self.sequence_length):
                sample = []
                
                for param_name in self.param_names:
                    pattern = self.failure_patterns[param_name]
                    
                    if scenario == 'healthy':
                        # Generate values mostly in optimal range
                        if np.random.random() < 0.8:  # 80% optimal
                            value = np.random.uniform(pattern['optimal_low'], pattern['optimal_high'])
                        else:  # 20% near-optimal
                            value = np.random.uniform(pattern['warning_low'], pattern['warning_high'])
                    
                    elif scenario == 'warning':
                        # Generate values in warning ranges
                        if np.random.random() < 0.5:
                            # Lower warning range
                            value = np.random.uniform(pattern['warning_low'], pattern['optimal_low'])
                        else:
                            # Upper warning range
                            value = np.random.uniform(pattern['optimal_high'], pattern['warning_high'])
                    
                    else:  # critical
                        # Generate values in critical ranges
                        if np.random.random() < 0.5:
                            # Below critical low
                            value = np.random.uniform(
                                pattern['critical_low'] - (pattern['critical_low'] * 0.1),
                                pattern['critical_low']
                            )
                        else:
                            # Above critical high
                            value = np.random.uniform(
                                pattern['critical_high'],
                                pattern['critical_high'] + (pattern['critical_high'] * 0.1)
                            )
                    
                    sample.append(value)
                
                sequence.append(sample)
            
            # Classify the last sample in the sequence
            health_status = self.classify_health_status(sequence[-1])
            
            sequences.append(sequence)
            labels.append(health_status)
        
        return np.array(sequences), np.array(labels)
    
    def create_model(self, input_shape):
        """Create LSTM model architecture"""
        print("🔄 Creating LSTM model architecture...")
        
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(3, activation='softmax')  # 3 classes: HEALTHY, WARNING, CRITICAL
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_model(self):
        """Complete model training pipeline"""
        print("🚀 Starting LSTM model retraining...")
        
        # Generate training data
        X, y = self.generate_training_data(10000)
        print(f"✅ Generated data shape: X={X.shape}, y={y.shape}")
        
        # Check class distribution
        unique, counts = np.unique(y, return_counts=True)
        print("📊 Class distribution:")
        for class_idx, count in zip(unique, counts):
            class_name = ['HEALTHY', 'WARNING', 'CRITICAL'][class_idx]
            print(f"   {class_name}: {count} samples ({count/len(y)*100:.1f}%)")
        
        # Reshape for scaling
        n_samples, n_timesteps, n_features = X.shape
        X_reshaped = X.reshape(-1, n_features)
        
        # Fit scaler and transform
        print("🔄 Fitting scaler...")
        X_scaled = self.scaler.fit_transform(X_reshaped)
        X_scaled = X_scaled.reshape(n_samples, n_timesteps, n_features)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📊 Training set: {X_train.shape}, Test set: {X_test.shape}")
        
        # Create model
        model = self.create_model((n_timesteps, n_features))
        print(f"🧠 Model architecture:")
        model.summary()
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.0001)
        ]
        
        # Train model
        print("🔄 Training model...")
        history = model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=50,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate model
        print("📊 Evaluating model...")
        train_loss, train_acc = model.evaluate(X_train, y_train, verbose=0)
        test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
        
        print(f"✅ Training accuracy: {train_acc:.4f}")
        print(f"✅ Test accuracy: {test_acc:.4f}")
        
        # Test with known optimal values
        print("\n🧪 Testing with optimal parameter values:")
        optimal_values = [28.0, 65.0, 120.0, 2200, 15.0, 225.0]  # Default optimal values
        test_sequence = np.array([optimal_values] * self.sequence_length).reshape(1, self.sequence_length, 6)
        test_sequence_scaled = self.scaler.transform(test_sequence.reshape(-1, 6)).reshape(1, self.sequence_length, 6)
        
        prediction = model.predict(test_sequence_scaled, verbose=0)
        predicted_class = np.argmax(prediction[0])
        predicted_prob = prediction[0]
        
        class_names = ['HEALTHY', 'WARNING', 'CRITICAL']
        print(f"   Predicted class: {class_names[predicted_class]} ({predicted_prob[predicted_class]:.3f} confidence)")
        print(f"   Probabilities: Healthy={predicted_prob[0]:.3f}, Warning={predicted_prob[1]:.3f}, Critical={predicted_prob[2]:.3f}")
        
        if predicted_class == 0:  # Should be HEALTHY
            print("   ✅ Correct! Model predicts HEALTHY for optimal values")
        else:
            print("   ❌ Wrong! Model should predict HEALTHY for optimal values")
        
        return model, history
    
    def save_model(self, model):
        """Save the trained model and scaler"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save model
        model_filename = f"retrained_lstm_model_{timestamp}.h5"
        model.save(model_filename)
        print(f"✅ Model saved as: {model_filename}")
        
        # Save scaler
        scaler_filename = f"retrained_scaler_{timestamp}.pkl"
        with open(scaler_filename, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"✅ Scaler saved as: {scaler_filename}")
        
        # Update the monitor to use the new model
        print("\n🔄 Updating monitor to use retrained model...")
        self.update_monitor_model_path(model_filename, scaler_filename)
        
        return model_filename, scaler_filename
    
    def update_monitor_model_path(self, model_filename, scaler_filename):
        """Update the monitor code to use the new model files"""
        # Read the current monitor file
        try:
            with open('enhanced_real_time_monitor.py', 'r') as f:
                content = f.read()
            
            # Update the model loading priority to use our new model first
            old_line = "model_files = ['enhanced_lstm_health_model.h5', 'new_lstm_health_model.h5', 'lstm_health_model.h5']"
            new_line = f"model_files = ['{model_filename}', 'enhanced_lstm_health_model.h5', 'new_lstm_health_model.h5', 'lstm_health_model.h5']"
            content = content.replace(old_line, new_line)
            
            old_scaler_line = "scaler_files = ['enhanced_scaler.pkl', 'new_scaler.pkl', 'scaler.pkl']"
            new_scaler_line = f"scaler_files = ['{scaler_filename}', 'enhanced_scaler.pkl', 'new_scaler.pkl', 'scaler.pkl']"
            content = content.replace(old_scaler_line, new_scaler_line)
            
            # Write back the updated content
            with open('enhanced_real_time_monitor.py', 'w') as f:
                f.write(content)
            
            print(f"✅ Updated monitor to prioritize: {model_filename}")
            
        except Exception as e:
            print(f"⚠️ Could not update monitor automatically: {e}")
            print(f"   Please manually update the model_files list to include: {model_filename}")
            print(f"   Please manually update the scaler_files list to include: {scaler_filename}")

def main():
    if not TENSORFLOW_AVAILABLE:
        print("❌ TensorFlow is required for model retraining")
        return
    
    print("🏭 LSTM Model Retraining with Correct Parameter Ranges")
    print("=" * 60)
    
    retrainer = ModelRetrainer()
    
    # Train the model
    model, history = retrainer.train_model()
    
    # Save the model
    model_file, scaler_file = retrainer.save_model(model)
    
    print("\n" + "=" * 60)
    print("🎉 Model retraining completed successfully!")
    print(f"📁 New model file: {model_file}")
    print(f"📁 New scaler file: {scaler_file}")
    print("\n💡 Next steps:")
    print("1. Restart the enhanced_real_time_monitor.py")
    print("2. Test with optimal parameter values")
    print("3. Verify that HEALTHY status is shown correctly")

if __name__ == "__main__":
    main()
