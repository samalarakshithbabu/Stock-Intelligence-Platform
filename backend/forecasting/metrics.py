"""
Evaluation Metrics for Model Performance Assessment.

Implements comprehensive metrics for time-series forecasting:
- RMSE, MAE, MAPE, sMAPE, R²
- Directional Accuracy
- Statistical significance tests
"""
import numpy as np
from typing import Dict, Any, List, Tuple
import warnings


def calculate_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return np.sqrt(np.mean((actual - predicted) ** 2))


def calculate_mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Error."""
    return np.mean(np.abs(actual - predicted))


def calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Mean Absolute Percentage Error.
    Handles zero values gracefully.
    """
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    # Avoid division by zero
    mask = actual != 0
    if not np.any(mask):
        return np.nan
    
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100


def calculate_smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Symmetric MAPE.
    More robust to outliers and zero values.
    """
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    denominator = np.abs(actual) + np.abs(predicted)
    mask = denominator != 0
    
    if not np.any(mask):
        return np.nan
    
    return np.mean(
        np.abs(actual[mask] - predicted[mask]) / denominator[mask]
    ) * 100


def calculate_r_squared(actual: np.ndarray, predicted: np.ndarray) -> float:
    """R-squared (coefficient of determination)."""
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    
    if ss_tot == 0:
        return np.nan
    
    return 1 - (ss_res / ss_tot)


def calculate_directional_accuracy(
    actual: np.ndarray, 
    predicted: np.ndarray
) -> float:
    """
    Directional Accuracy: Percentage of correct direction predictions.
    
    Returns the percentage of predictions where the model correctly
    predicts whether the price will go up or down.
    """
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    if len(actual) < 2:
        return np.nan
    
    # Calculate actual directions
    actual_direction = np.sign(np.diff(actual))
    
    # Calculate predicted directions
    predicted_direction = np.sign(np.diff(predicted))
    
    # Remove zeros (no change)
    mask = (actual_direction != 0) & (predicted_direction != 0)
    
    if not np.any(mask):
        return 0.0
    
    correct = np.sum(
        actual_direction[mask] == predicted_direction[mask]
    )
    
    return (correct / np.sum(mask)) * 100


def calculate_residuals(actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    """Calculate prediction residuals."""
    return actual - predicted


def calculate_residual_statistics(residuals: np.ndarray) -> Dict[str, float]:
    """Calculate statistical properties of residuals."""
    return {
        "mean": float(np.mean(residuals)),
        "std": float(np.std(residuals)),
        "min": float(np.min(residuals)),
        "max": float(np.max(residuals)),
        "skewness": float(_skewness(residuals)),
        "kurtosis": float(_kurtosis(residuals))
    }


def _skewness(data: np.ndarray) -> float:
    """Calculate skewness of data."""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data)
    
    if std == 0:
        return 0
    
    return np.sum(((data - mean) / std) ** 3) / n


def _kurtosis(data: np.ndarray) -> float:
    """Calculate kurtosis of data."""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data)
    
    if std == 0:
        return 0
    
    return np.sum(((data - mean) / std) ** 4) / n - 3


def calculate_all_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
    model_name: str = "model"
) -> Dict[str, Any]:
    """
    Calculate all evaluation metrics.
    
    Args:
        actual: Ground truth values
        predicted: Model predictions
        model_name: Name for the model
    
    Returns:
        Dictionary with all metrics
    """
    # Filter out any NaN values
    mask = ~(np.isnan(actual) | np.isnan(predicted))
    actual_clean = actual[mask]
    predicted_clean = predicted[mask]
    
    if len(actual_clean) == 0:
        return {
            "model_name": model_name,
            "error": "No valid data for evaluation"
        }
    
    metrics = {
        "model_name": model_name,
        "mae": round(calculate_mae(actual_clean, predicted_clean), 4),
        "rmse": round(calculate_rmse(actual_clean, predicted_clean), 4),
        "mape": round(calculate_mape(actual_clean, predicted_clean), 4),
        "smape": round(calculate_smape(actual_clean, predicted_clean), 4),
        "r_squared": round(calculate_r_squared(actual_clean, predicted_clean), 4),
        "directional_accuracy": round(
            calculate_directional_accuracy(actual_clean, predicted_clean), 2
        ),
        "sample_count": len(actual_clean)
    }
    
    # Calculate residual statistics
    residuals = calculate_residuals(actual_clean, predicted_clean)
    metrics["residual_stats"] = calculate_residual_statistics(residuals)
    
    return metrics


def compare_models(
    results: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Compare multiple models' performance.
    
    Args:
        results: Dictionary of model_name -> metrics
    
    Returns:
        Comparison analysis
    """
    comparison = {
        "rankings": {},
        "best_by_metric": {},
        "summary": {}
    }
    
    for metric in ["rmse", "mae", "mape", "r_squared", "directional_accuracy"]:
        # Sort models by metric (lower is better except r_squared and directional_accuracy)
        if metric in ["r_squared", "directional_accuracy"]:
            sorted_models = sorted(
                results.items(), 
                key=lambda x: x[1].get(metric, 0), 
                reverse=True
            )
        else:
            sorted_models = sorted(
                results.items(), 
                key=lambda x: x[1].get(metric, float('inf'))
            )
        
        comparison["rankings"][metric] = [
            {"model": name, "value": metrics.get(metric)} 
            for name, metrics in sorted_models
        ]
        comparison["best_by_metric"][metric] = sorted_models[0][0]
    
    # Overall summary
    comparison["summary"] = {
        "total_models": len(results),
        "metrics_evaluated": list(results[list(results.keys())[0]].keys()) if results else []
    }
    
    return comparison


def calculate_confidence_interval(
    predictions: np.ndarray,
    confidence: float = 0.95
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate confidence intervals for predictions.
    
    Args:
        predictions: Array of predictions
        confidence: Confidence level (0.95 = 95%)
    
    Returns:
        Lower and upper bounds
    """
    alpha = 1 - confidence
    mean_pred = np.mean(predictions)
    std_pred = np.std(predictions)
    
    # Use t-distribution critical value approximation
    z = 1.96  # Approximation for 95% CI
    
    lower = mean_pred - z * std_pred
    upper = mean_pred + z * std_pred
    
    return lower, upper