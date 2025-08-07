import os

import numpy as np

# Step 1: Standardize the data


def standardize_data(data):
    mean = np.mean(data, axis=0)
    std_dev = np.std(data, axis=0)
    return (data - mean) / std_dev


# Step 2: Compute the covariance matrix


def compute_covariance_matrix(data):
    return np.cov(data, rowvar=False)


# Step 3: Perform eigenvalue decomposition of the covariance matrix


def eigen_decomposition(covariance_matrix):
    eigenvalues, eigenvectors = np.linalg.eig(covariance_matrix)
    return eigenvalues, eigenvectors


# Step 4: Sort the eigenvalues and their corresponding eigenvectors


def sort_eigenvalues_eigenvectors(eigenvalues, eigenvectors):
    idx = eigenvalues.argsort()[::-1]
    sorted_eigenvalues = eigenvalues[idx]
    sorted_eigenvectors = eigenvectors[:, idx]
    return sorted_eigenvalues, sorted_eigenvectors


# Step 5: Select the top k eigenvectors (principal components)


def select_top_k_components(eigenvectors, k):
    return eigenvectors[:, :k]


# Step 6: Transform the original data to the new subspace


def transform_data(data, components):
    return data.dot(components)


# Function to perform PCA


def pca(data, k):
    print(data[:10])
    data_standardized = standardize_data(data)
    print(data_standardized[:10])
    covariance_matrix = compute_covariance_matrix(data_standardized)
    print(covariance_matrix)
    eigenvalues, eigenvectors = eigen_decomposition(covariance_matrix)
    print(eigenvalues, eigenvectors)
    _, sorted_eigenvectors = sort_eigenvalues_eigenvectors(eigenvalues, eigenvectors)
    top_k_components = select_top_k_components(sorted_eigenvectors, k)
    data_pca = transform_data(data_standardized, top_k_components)
    return data_pca


def get_environment(config, value: str, env: str, error_msg: str) -> str:
    if value in config:
        token = config[value].value
    else:
        token = os.environ.get(env)
    if not token:
        raise ValueError(error_msg)
    return token


def strip_non_letters(text: str) -> str:
    """Strip non-letter characters from text to create valid class names."""
    import re

    return re.sub(r"\W", "", text)
