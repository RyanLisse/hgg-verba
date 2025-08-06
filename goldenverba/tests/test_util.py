import numpy as np
from goldenverba.components.util import (
    standardize_data,
    pca
)


def test_pca_components():
    # Create sample data
    X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
    k = 2

    # Test PCA transformation
    X_pca = pca(X, k)
    
    # Check output shape
    assert X_pca.shape[0] == X.shape[0]  # Same number of samples
    assert X_pca.shape[1] == k  # Reduced to k components

def test_standardize_data():
    X = np.array([[1, 2], [3, 4], [5, 6]])
    X_std = standardize_data(X)
    
    # Check if standardized data has mean close to 0 and std close to 1
    assert np.allclose(np.mean(X_std, axis=0), 0, atol=1e-10)
    assert np.allclose(np.std(X_std, axis=0), 1, atol=1e-10)
