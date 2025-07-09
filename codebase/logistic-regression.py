import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
import os
from sklearn.model_selection import GridSearchCV


def train_logistic_regression(train_df, test_df):
    X_train = train_df.drop("sentiment", axis=1)
    Y_train = train_df["sentiment"]

    X_test = test_df.drop("sentiment", axis=1)
    Y_test = test_df["sentiment"]

    model = LogisticRegression(max_iter=1000,random_state=42,solver="saga",verbose=1,tol=1e-2)
    model.fit(X_train, Y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(Y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")

    print("\nClassification Report:")
    print(classification_report(Y_test, y_pred))

    print("\nConfusion Matrix:")
    print(confusion_matrix(Y_test, y_pred))

    # Create visualization
    for class_idx in range(len(model.classes_)):
        visualize_logistic_curve(model, X_test, Y_test, class_of_interest=class_idx)
    
    return model

def load_data():
    train_df = pd.read_csv("../data/train-data.csv")
    test_df = pd.read_csv("../data/test-data.csv")
    val_df = pd.read_csv("../data/val-data.csv")

    return train_df, test_df, val_df

def visualize_logistic_curve(model, X_test, Y_test, class_of_interest=0):
    """
    Visualize the logistic regression sigmoid curve for a specific class
    """
    # Create directory for visualizations
    os.makedirs('../visualizations', exist_ok=True)
    
    # For multiclass, we'll focus on the probability of one class
    if len(np.unique(Y_test)) > 2:
        # Get probability estimates for the class of interest
        probs = model.predict_proba(X_test)[:, class_of_interest]
        
        # Get the decision values (log-odds)
        if hasattr(model, 'decision_function'):
            decision_values = model.decision_function(X_test)
            # For multiclass, choose the column corresponding to class_of_interest
            if decision_values.ndim > 1:
                decision_values = decision_values[:, class_of_interest]
        else:
            # Approximate log-odds from probabilities
            decision_values = np.log(probs / (1 - probs))
    else:
        # Binary case
        probs = model.predict_proba(X_test)[:, 1]
        decision_values = model.decision_function(X_test)
    
    # Sort for a smooth curve
    sorted_idx = np.argsort(decision_values)
    sorted_decision = decision_values[sorted_idx]
    sorted_probs = probs[sorted_idx]
    
    # Create figure
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_decision, sorted_probs, 'y-', linewidth=3)
    
    # Draw horizontal and vertical lines for a specific probability threshold (0.75)
    threshold_prob = 0.75
    # Find closest point to threshold_prob
    idx = np.abs(sorted_probs - threshold_prob).argmin()
    threshold_decision = sorted_decision[idx]
    
    # Draw lines
    plt.axhline(y=threshold_prob, color='y', linestyle='--', alpha=0.7)
    plt.axvline(x=threshold_decision, color='y', linestyle='--', alpha=0.7)
    plt.plot(threshold_decision, threshold_prob, 'yo', markersize=8)
    
    # Add text
    plt.text(threshold_decision + 0.5, threshold_prob, str(threshold_prob), 
             color='yellow', fontsize=14, verticalalignment='center')
    
    # Set axis limits and labels
    plt.xlim(sorted_decision.min() - 1, sorted_decision.max() + 1)
    plt.ylim(-0.05, 1.05)
    plt.xlabel('Decision Function Value (Log-odds)', color='white')
    plt.ylabel('Probability', color='white')
    plt.title(f'Logistic Regression Curve for Class {class_of_interest}', color='white')
    
    # Set background color to black
    plt.gca().set_facecolor('black')
    fig = plt.gcf()
    fig.patch.set_facecolor('black')
    
    # Set ticks and grid colors
    plt.tick_params(colors='white')
    for spine in plt.gca().spines.values():
        spine.set_color('white')
    
    # Add reference lines
    plt.axhline(y=1, color='white', linestyle='dotted', alpha=0.5)
    plt.axhline(y=0, color='white', linestyle='dotted', alpha=0.5)
    
    plt.savefig(f'../visualizations/logistic_curve_class_{class_of_interest}.png', 
                facecolor='black', bbox_inches='tight')
    plt.close()
    
    print(f"Logistic curve visualization saved to '../visualizations/logistic_curve_class_{class_of_interest}.png'")

if __name__ == "__main__":
    train_df, test_df, val_df = load_data()

    model = train_logistic_regression(train_df, test_df)
