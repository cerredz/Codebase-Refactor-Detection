import pandas as pd
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize, StandardScaler
import os
from sklearn.model_selection import GridSearchCV


def train_svm(train_df, test_df):
    X_train = train_df.drop("sentiment", axis=1)
    Y_train = train_df["sentiment"]

    X_test = test_df.drop("sentiment", axis=1)
    Y_test = test_df["sentiment"]

    # Scale features for SVM (important for SVM performance)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # SVM model with probability estimation enabled
    model = SVC(kernel='rbf', random_state=42, probability=True, verbose=True)
    model.fit(X_train_scaled, Y_train)

    y_pred = model.predict(X_test_scaled)

    accuracy = accuracy_score(Y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")

    print("\nClassification Report:")
    print(classification_report(Y_test, y_pred))

    print("\nConfusion Matrix:")
    print(confusion_matrix(Y_test, y_pred))

    # Create visualization
    for class_idx in range(len(model.classes_)):
        visualize_svm_decision_boundary(model, scaler, X_test, Y_test, class_of_interest=class_idx)
    
    return model, scaler

def load_data():
    train_df = pd.read_csv("../data/train-data.csv")
    test_df = pd.read_csv("../data/test-data.csv")
    val_df = pd.read_csv("../data/val-data.csv")

    return train_df, test_df, val_df

def visualize_svm_decision_boundary(model, scaler, X_test, Y_test, class_of_interest=0):
    """
    Visualize the SVM decision boundary and probability estimates for a specific class
    """
    # Create directory for visualizations
    os.makedirs('../visualizations', exist_ok=True)
    
    # Scale the test data
    X_test_scaled = scaler.transform(X_test)
    
    # Get probability estimates for the class of interest
    probs = model.predict_proba(X_test_scaled)[:, class_of_interest]
    
    # Get decision function values (distance from hyperplane)
    if len(np.unique(Y_test)) > 2:
        # For multiclass, decision_function returns shape (n_samples, n_classes)
        decision_values = model.decision_function(X_test_scaled)
        if decision_values.ndim > 1:
            decision_values = decision_values[:, class_of_interest]
    else:
        # For binary classification
        decision_values = model.decision_function(X_test_scaled)
        if class_of_interest == 0:
            decision_values = -decision_values  # Flip for class 0
    
    # Sort for a smooth curve
    sorted_idx = np.argsort(decision_values)
    sorted_decision = decision_values[sorted_idx]
    sorted_probs = probs[sorted_idx]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.patch.set_facecolor('black')
    
    # Plot 1: Decision function vs Probability
    ax1.plot(sorted_decision, sorted_probs, 'c-', linewidth=3, label='SVM Probability')
    
    # Draw horizontal and vertical lines for a specific probability threshold (0.75)
    threshold_prob = 0.75
    idx = np.abs(sorted_probs - threshold_prob).argmin()
    threshold_decision = sorted_decision[idx]
    
    ax1.axhline(y=threshold_prob, color='c', linestyle='--', alpha=0.7)
    ax1.axvline(x=threshold_decision, color='c', linestyle='--', alpha=0.7)
    ax1.plot(threshold_decision, threshold_prob, 'co', markersize=8)
    
    ax1.text(threshold_decision + 0.1, threshold_prob + 0.05, f'{threshold_prob}', 
             color='cyan', fontsize=12, verticalalignment='bottom')
    
    ax1.set_xlim(sorted_decision.min() - 0.5, sorted_decision.max() + 0.5)
    ax1.set_ylim(-0.05, 1.05)
    ax1.set_xlabel('Decision Function Value', color='white')
    ax1.set_ylabel('Probability', color='white')
    ax1.set_title(f'SVM Decision Function vs Probability\nClass {class_of_interest}', color='white')
    ax1.set_facecolor('black')
    ax1.tick_params(colors='white')
    for spine in ax1.spines.values():
        spine.set_color('white')
    
    # Add decision boundary reference
    ax1.axvline(x=0, color='red', linestyle=':', alpha=0.7, label='Decision Boundary')
    ax1.legend(facecolor='black', edgecolor='white', labelcolor='white')
    
    # Plot 2: Support Vector distribution
    # Get support vector indices
    support_vectors = model.support_
    
    # Create histogram of decision values
    ax2.hist(decision_values, bins=50, alpha=0.7, color='cyan', edgecolor='white')
    ax2.axvline(x=0, color='red', linestyle=':', linewidth=2, label='Decision Boundary')
    
    # Highlight support vector region
    if len(support_vectors) > 0:
        sv_decisions = decision_values[support_vectors] if len(support_vectors) <= len(decision_values) else []
        if len(sv_decisions) > 0:
            ax2.hist(sv_decisions, bins=20, alpha=0.5, color='yellow', 
                    edgecolor='orange', label='Support Vectors')
    
    ax2.set_xlabel('Decision Function Value', color='white')
    ax2.set_ylabel('Frequency', color='white')
    ax2.set_title(f'Distribution of Decision Values\nClass {class_of_interest}', color='white')
    ax2.set_facecolor('black')
    ax2.tick_params(colors='white')
    for spine in ax2.spines.values():
        spine.set_color('white')
    ax2.legend(facecolor='black', edgecolor='white', labelcolor='white')
    
    plt.tight_layout()
    plt.savefig(f'../visualizations/svm_analysis_class_{class_of_interest}.png', 
                facecolor='black', bbox_inches='tight')
    plt.close()
    
    print(f"SVM analysis visualization saved to '../visualizations/svm_analysis_class_{class_of_interest}.png'")

def hyperparameter_tuning(train_df, val_df):
    """
    Perform hyperparameter tuning for SVM
    """
    X_train = train_df.drop("sentiment", axis=1)
    Y_train = train_df["sentiment"]
    
    X_val = val_df.drop("sentiment", axis=1)
    Y_val = val_df["sentiment"]
    
    # Combine train and validation for cross-validation
    X_combined = pd.concat([X_train, X_val])
    Y_combined = pd.concat([Y_train, Y_val])
    
    # Scale features
    scaler = StandardScaler()
    X_combined_scaled = scaler.fit_transform(X_combined)
    
    # Define parameter grid
    param_grid = {
        'C': [0.1, 1, 10, 100],
        'kernel': ['rbf', 'poly', 'sigmoid'],
        'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1]
    }
    
    # Grid search with cross-validation
    svm = SVC(random_state=42, probability=True)
    grid_search = GridSearchCV(svm, param_grid, cv=5, scoring='accuracy', 
                              verbose=1, n_jobs=-1)
    
    print("Starting hyperparameter tuning...")
    grid_search.fit(X_combined_scaled, Y_combined)
    
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
    
    return grid_search.best_estimator_, scaler

if __name__ == "__main__":
    train_df, test_df, val_df = load_data()

    # Option 1: Train with default parameters
    print("Training SVM with default parameters...")
    model, scaler = train_svm(train_df, test_df)
    
    # Option 2: Train with hyperparameter tuning (uncomment to use)
    # print("\nTraining SVM with hyperparameter tuning...")
    # best_model, best_scaler = hyperparameter_tuning(train_df, val_df)
    # 
    # # Test the best model
    # X_test = test_df.drop("sentiment", axis=1)
    # Y_test = test_df["sentiment"]
    # X_test_scaled = best_scaler.transform(X_test)
    # y_pred_best = best_model.predict(X_test_scaled)
    # accuracy_best = accuracy_score(Y_test, y_pred_best)
    # print(f"\nBest model test accuracy: {accuracy_best:.4f}")