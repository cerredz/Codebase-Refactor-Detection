import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize, StandardScaler
import os
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.decomposition import PCA
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')


def preprocess_features(X_train, X_test, X_val, method='standard'):
    """
    CONCEPT: Feature Preprocessing
    
    Why this helps: Different features might have very different scales (e.g., age vs income).
    Logistic regression can be sensitive to these scale differences.
    
    Methods:
    - 'standard': Standardize features (mean=0, std=1)
    - 'polynomial': Create polynomial combinations of features
    - 'both': Apply both standardization and polynomial features
    """
    if method == 'none':
        return X_train, X_test, X_val, None
    
    print(f"Applying {method} preprocessing...")
    
    if method == 'standard':
        scaler = StandardScaler()
        X_train_processed = scaler.fit_transform(X_train)
        X_test_processed = scaler.transform(X_test)
        X_val_processed = scaler.transform(X_val)
        return X_train_processed, X_test_processed, X_val_processed, scaler
    
    elif method == 'polynomial':
        # Create polynomial features (combinations like x1*x2, x1^2, etc.)
        poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
        X_train_processed = poly.fit_transform(X_train)
        X_test_processed = poly.transform(X_test)
        X_val_processed = poly.transform(X_val)
        print(f"Created {X_train_processed.shape[1]} polynomial features from {X_train.shape[1]} original features")
        return X_train_processed, X_test_processed, X_val_processed, poly
    
    elif method == 'both':
        # First create polynomial features, then standardize
        poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
        X_train_poly = poly.fit_transform(X_train)
        X_test_poly = poly.transform(X_test)
        X_val_poly = poly.transform(X_val)
        
        scaler = StandardScaler()
        X_train_processed = scaler.fit_transform(X_train_poly)
        X_test_processed = scaler.transform(X_test_poly)
        X_val_processed = scaler.transform(X_val_poly)
        
        print(f"Created {X_train_processed.shape[1]} polynomial features, then standardized")
        return X_train_processed, X_test_processed, X_val_processed, (poly, scaler)


def feature_selection(X_train, Y_train, X_test, X_val, method='univariate', k=50):
    """
    CONCEPT: Feature Selection
    
    Why this helps: Not all features are useful. Some might be noise or irrelevant.
    Removing bad features can improve accuracy and reduce overfitting.
    
    Methods:
    - 'univariate': Select features based on statistical tests (fastest)
    - 'rfe': Recursive Feature Elimination (more thorough, slower)
    - 'pca': Principal Component Analysis (creates new features from combinations)
    """
    print(f"Applying {method} feature selection (k={k})...")
    
    if method == 'univariate':
        # Select features based on ANOVA F-test scores
        selector = SelectKBest(score_func=f_classif, k=min(k, X_train.shape[1]))
        X_train_selected = selector.fit_transform(X_train, Y_train)
        X_test_selected = selector.transform(X_test)
        X_val_selected = selector.transform(X_val)
        
        print(f"Selected {X_train_selected.shape[1]} best features out of {X_train.shape[1]}")
        return X_train_selected, X_test_selected, X_val_selected, selector
    
    elif method == 'rfe':
        # Recursively eliminate features by training models
        base_model = LogisticRegression(max_iter=1000, random_state=42)
        selector = RFE(base_model, n_features_to_select=min(k, X_train.shape[1]))
        X_train_selected = selector.fit_transform(X_train, Y_train)
        X_test_selected = selector.transform(X_test)
        X_val_selected = selector.transform(X_val)
        
        print(f"RFE selected {X_train_selected.shape[1]} features out of {X_train.shape[1]}")
        return X_train_selected, X_test_selected, X_val_selected, selector
    
    elif method == 'pca':
        # Create new features that capture most variance
        pca = PCA(n_components=min(k, X_train.shape[1], X_train.shape[0]))
        X_train_selected = pca.fit_transform(X_train)
        X_test_selected = pca.transform(X_test)
        X_val_selected = pca.transform(X_val)
        
        explained_variance = np.sum(pca.explained_variance_ratio_)
        print(f"PCA kept {X_train_selected.shape[1]} components explaining {explained_variance:.2%} of variance")
        return X_train_selected, X_test_selected, X_val_selected, pca


def hyperparameter_tuning(X_train, Y_train):
    """
    CONCEPT: Hyperparameter Tuning for Logistic Regression
    
    Key parameters to tune:
    - C: Regularization strength (lower C = more regularization = simpler model)
    - solver: Algorithm used to optimize (different solvers work better for different data)
    - max_iter: Maximum iterations (prevents early stopping due to non-convergence)
    - penalty: Type of regularization (L1, L2, or both)
    """
    print("Starting hyperparameter tuning...")
    
    param_grid = {
        'C': [0.001, 0.01, 0.1, 1, 10, 100],  # Regularization strength
        'solver': ['liblinear', 'saga', 'lbfgs'],  # Optimization algorithms
        'max_iter': [1000, 2000],  # Maximum iterations
        'penalty': ['l1', 'l2', 'elasticnet']  # Regularization types
    }
    
    # Create base model
    base_model = LogisticRegression(random_state=42, verbose=0)
    
    # Grid search with cross-validation
    grid_search = GridSearchCV(
        base_model, 
        param_grid, 
        cv=5,  # 5-fold cross-validation
        scoring='accuracy',
        verbose=1,
        n_jobs=-1  # Use all CPU cores
    )
    
    grid_search.fit(X_train, Y_train)
    
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
    
    return grid_search.best_estimator_


def train_improved_logistic_regression(train_df, test_df, val_df, 
                                     preprocessing='standard',
                                     feature_sel_method='univariate',
                                     feature_sel_k=50,
                                     tune_hyperparams=True):
    """
    Enhanced logistic regression with multiple improvement techniques
    """
    print("=== TRAINING IMPROVED LOGISTIC REGRESSION ===")
    
    # Separate features and labels
    X_train = train_df.drop("sentiment", axis=1)
    Y_train = train_df["sentiment"]
    X_test = test_df.drop("sentiment", axis=1)
    Y_test = test_df["sentiment"]
    X_val = val_df.drop("sentiment", axis=1)
    Y_val = val_df["sentiment"]
    
    print(f"Original data shape: {X_train.shape}")
    
    # Step 1: Preprocessing
    X_train_proc, X_test_proc, X_val_proc, preprocessor = preprocess_features(
        X_train, X_test, X_val, method=preprocessing
    )
    
    # Step 2: Feature Selection
    if feature_sel_method != 'none':
        X_train_final, X_test_final, X_val_final, selector = feature_selection(
            X_train_proc, Y_train, X_test_proc, X_val_proc, 
            method=feature_sel_method, k=feature_sel_k
        )
    else:
        X_train_final, X_test_final, X_val_final = X_train_proc, X_test_proc, X_val_proc
        selector = None
    
    print(f"Final training data shape: {X_train_final.shape}")
    
    # Step 3: Model Training
    if tune_hyperparams:
        model = hyperparameter_tuning(X_train_final, Y_train)
    else:
        print("Training with default parameters...")
        model = LogisticRegression(max_iter=1000, random_state=42, solver="saga", verbose=1, tol=1e-2)
        model.fit(X_train_final, Y_train)
    
    # Step 4: Evaluation
    print("\n=== VALIDATION SET PERFORMANCE ===")
    val_pred = model.predict(X_val_final)
    val_accuracy = accuracy_score(Y_val, val_pred)
    print(f"Validation Accuracy: {val_accuracy:.4f}")
    
    print("\n=== TEST SET PERFORMANCE ===")
    test_pred = model.predict(X_test_final)
    test_accuracy = accuracy_score(Y_test, test_pred)
    print(f"Test Accuracy: {test_accuracy:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(Y_test, test_pred))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(Y_test, test_pred))
    
    # Cross-validation score for more robust evaluation
    cv_scores = cross_val_score(model, X_train_final, Y_train, cv=5)
    print(f"\nCross-validation scores: {cv_scores}")
    print(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Visualization
    for class_idx in range(len(model.classes_)):
        visualize_logistic_curve(model, X_test_final, Y_test, class_of_interest=class_idx)
    
    return {
        'model': model,
        'preprocessor': preprocessor,
        'selector': selector,
        'test_accuracy': test_accuracy,
        'val_accuracy': val_accuracy,
        'cv_scores': cv_scores
    }


def compare_methods(train_df, test_df, val_df):
    """
    CONCEPT: A/B Testing Different Approaches
    
    This function systematically compares different combinations of techniques
    to see which works best for your specific dataset.
    """
    print("=== COMPARING DIFFERENT IMPROVEMENT METHODS ===")
    
    methods_to_test = [
        ('baseline', 'none', 'none', False),
        ('standardized', 'standard', 'none', False),
        ('standardized + tuned', 'standard', 'none', True),
        ('standard + feature_sel', 'standard', 'univariate', True),
        ('polynomial + standard', 'both', 'univariate', True),
    ]
    
    results = []
    
    for name, preprocessing, feature_sel, tune_hp in methods_to_test:
        print(f"\n--- Testing: {name} ---")
        try:
            result = train_improved_logistic_regression(
                train_df, test_df, val_df,
                preprocessing=preprocessing,
                feature_sel_method=feature_sel,
                feature_sel_k=50,
                tune_hyperparams=tune_hp
            )
            results.append((name, result['test_accuracy'], result['val_accuracy']))
        except Exception as e:
            print(f"Error with {name}: {e}")
            results.append((name, 0, 0))
    
    # Display comparison
    print("\n=== COMPARISON RESULTS ===")
    print("Method                    | Test Acc | Val Acc")
    print("-" * 45)
    for name, test_acc, val_acc in results:
        print(f"{name:<25} | {test_acc:.4f}   | {val_acc:.4f}")
    
    # Find best method
    best_method = max(results, key=lambda x: x[1])
    print(f"\nBest method: {best_method[0]} with test accuracy: {best_method[1]:.4f}")
    
    return results


def load_data():
    train_df = pd.read_csv("../data/train-data.csv")
    test_df = pd.read_csv("../data/test-data.csv")
    val_df = pd.read_csv("../data/val-data.csv")
    return train_df, test_df, val_df


def visualize_logistic_curve(model, X_test, Y_test, class_of_interest=0):
    """
    Visualize the logistic regression sigmoid curve for a specific class
    (Same as original, but works with processed features)
    """
    os.makedirs('../visualizations', exist_ok=True)
    
    if len(np.unique(Y_test)) > 2:
        probs = model.predict_proba(X_test)[:, class_of_interest]
        if hasattr(model, 'decision_function'):
            decision_values = model.decision_function(X_test)
            if decision_values.ndim > 1:
                decision_values = decision_values[:, class_of_interest]
        else:
            decision_values = np.log(probs / (1 - probs + 1e-8))  # Added small epsilon to avoid division by zero
    else:
        probs = model.predict_proba(X_test)[:, 1]
        decision_values = model.decision_function(X_test)
    
    sorted_idx = np.argsort(decision_values)
    sorted_decision = decision_values[sorted_idx]
    sorted_probs = probs[sorted_idx]
    
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_decision, sorted_probs, 'y-', linewidth=3)
    
    threshold_prob = 0.75
    idx = np.abs(sorted_probs - threshold_prob).argmin()
    threshold_decision = sorted_decision[idx]
    
    plt.axhline(y=threshold_prob, color='y', linestyle='--', alpha=0.7)
    plt.axvline(x=threshold_decision, color='y', linestyle='--', alpha=0.7)
    plt.plot(threshold_decision, threshold_prob, 'yo', markersize=8)
    
    plt.text(threshold_decision + 0.5, threshold_prob, str(threshold_prob), 
             color='yellow', fontsize=14, verticalalignment='center')
    
    plt.xlim(sorted_decision.min() - 1, sorted_decision.max() + 1)
    plt.ylim(-0.05, 1.05)
    plt.xlabel('Decision Function Value (Log-odds)', color='white')
    plt.ylabel('Probability', color='white')
    plt.title(f'Improved Logistic Regression Curve for Class {class_of_interest}', color='white')
    
    plt.gca().set_facecolor('black')
    fig = plt.gcf()
    fig.patch.set_facecolor('black')
    
    plt.tick_params(colors='white')
    for spine in plt.gca().spines.values():
        spine.set_color('white')
    
    plt.axhline(y=1, color='white', linestyle='dotted', alpha=0.5)
    plt.axhline(y=0, color='white', linestyle='dotted', alpha=0.5)
    
    plt.savefig(f'../visualizations/improved_logistic_curve_class_{class_of_interest}.png', 
                facecolor='black', bbox_inches='tight')
    plt.close()
    
    print(f"Improved logistic curve visualization saved to '../visualizations/improved_logistic_curve_class_{class_of_interest}.png'")


if __name__ == "__main__":
    train_df, test_df, val_df = load_data()
    
    # Option 1: Compare all methods to find the best one
    print("Comparing different improvement methods...")
    results = compare_methods(train_df, test_df, val_df)
    
    # Option 2: Train with specific settings (uncomment to use)
    # print("\nTraining with specific improvements...")
    # final_result = train_improved_logistic_regression(
    #     train_df, test_df, val_df,
    #     preprocessing='standard',
    #     feature_sel_method='univariate',
    #     feature_sel_k=50,
    #     tune_hyperparams=True
    # )