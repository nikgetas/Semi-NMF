#####################################################################################
# HMM algorithm for clustering Mixture Model and visualization
#
# Date: Jan. 29, 2019
# Author: Da Zhi
#####################################################################################
import matplotlib.pyplot as plt
import scipy.io as spio
import numpy as np
from scipy.stats import multivariate_normal

DEBUG = True  # global debugging flag


# -------------------------------
# Global debugging flag - DEBUG
# -------------------------------
def debug(*args, **kwargs):
    global DEBUG
    if DEBUG:
        print(*args, **kwargs)


# -------------------------------------------------------------------
# Calculate the normal of probability of Xn given mu and covariance
# for the kth model using function 'multivariate_normal', this
# function is similar to 'mvnpdf' in MATLAB
# Input: Y - data points
#        mu_k - the mu array of k models
#        cov_k - the covariance of k models
# Return: norm.pdf(Y) (1-D array)
# -------------------------------------------------------------------
def phi(data, mu_k, cov_k):
    norm = multivariate_normal(mean=mu_k, cov=cov_k)
    return norm.pdf(data)


# ---------------------------------------------------------------------------------
# E - Step：Calculate the expectation of each of the model
# Input Parameters: Y - the matrix of data points with shape (400, 1)
#                   mu - the mean of each clusters
#                   cov - the covariance
#                   pi - cluster probability distribution of each point
# Return: gamma - the probability of data sample is from the k clusters
#         loglikelihood - the loglikelihood of current iteration
# ---------------------------------------------------------------------------------
def Expectation(Y, mu, cov, pi):
    # number of samples (data points)
    N = Y.shape[0]
    # number of models (clusters)
    K = pi.shape[0]
    loglikelihood = 0

    # The number of samples and mixture model are restricted equal to 1 to avoid different return types
    assert N > 1, "There should be more than one data sample"
    assert K > 1, "There should be more than one gaussian mixture model"

    # Initialize gamma, size of (400, k)
    gamma = np.mat(np.zeros((N, K)))

    # Calculate the probability of occurrence of all samples in each model,
    # row corresponding samples, column corresponding models
    prob = np.zeros((N, K))
    for k in range(K):
        prob[:, k] = phi(Y, mu[k], cov[k])
    prob = np.mat(prob)

    # Calculate the gamma of each model to each sample
    for k in range(K):
        gamma[:, k] = pi[k] * prob[:, k]

    # --------------------------------------------------------
    # Compute the log likelihood in current E-step iteration
    # --------------------------------------------------------
    for i in range(N):
        sum1data = np.log(np.sum(gamma[i, :]))
        loglikelihood += sum1data
        gamma[i, :] /= np.sum(gamma[i, :])

    return gamma, loglikelihood


# -----------------------------------------------------------------------
# M - Step：iteration computation of the probability distribution
#           to maximize the expectation
# Input parameters: Y - input data points matrix
#                   gamma - the result from E-step
# Return: new mu, covariance, and probability distribution pi
# -----------------------------------------------------------------------
def maximization(Y, gamma):
    # get shape of input data matrix, k for initialization
    N, D = Y.shape
    K = gamma.shape[1]
    mu = np.zeros((K, D))
    cov = []
    pi = np.zeros(K)

    # Update mu, cov, and pi for each of the models (clusters)
    for k in range(K):
        Nk = np.sum(gamma[:, k])
        # update mu, get the mean of each of the column
        for d in range(D):
            mu[k, d] = np.sum(np.multiply(gamma[:, k], Y[:, d])) / Nk
        # updata covariance
        cov_k = np.mat(np.zeros((D, D)))
        for i in range(N):
            cov_k += gamma[i, k] * (Y[i] - mu[k]).T * (Y[i] - mu[k]) / Nk
        cov.append(cov_k)
        # update pi
        pi[k] = Nk / N
    cov = np.array(cov)
    return mu, cov, pi


# ---------------------------------------------
# Data pre-processing
# Scaling all point data within [0, 1]
# ---------------------------------------------
def scale_data(Y):
    for i in range(Y.shape[1]):
        max_ = Y[:, i].max()
        min_ = Y[:, i].min()
        Y[:, i] = (Y[:, i] - min_) / (max_ - min_)
    debug("Data scaled.")
    return Y


# ---------------------------------------------------------------------
# Initialization the parameters of mixture model
# Input parameters: shape - the shape of data points (400, 2)
#                   K - the number of models (clusters)
# Return: mu - randomly generate, size of (k, 2)
#         covariance - k covariance matrices - identity
#         pi - the initial probability distribution - 1/k
# ---------------------------------------------------------------------
def init_params(shape, k):
    N, D = shape
    mu = np.random.rand(k, D)
    cov = np.array([np.eye(D)] * k)
    pi = np.array([1.0 / k] * k)
    debug("Parameters initialized.")
    debug("mu:", mu, "cov:", cov, "pi:", pi, sep="\n")
    return mu, cov, pi


# ------------------------------------------------------------------
# The main entry of the EM algorithm for mixture model
# Input: Y - the matrix of data input
#        k - the number of gaussian model (clusters)
#        time - the number of iteration
# Return: the final mu, cov, pi, and the array of loglikelihood
# ------------------------------------------------------------------
def MM_EM(datapoint, k, times):
    datapoint = scale_data(datapoint)
    mu, cov, pi = init_params(datapoint.shape, k)
    likelihoodarray = []
    for i in range(times):
        gamma, loglikelihood = Expectation(datapoint, mu, cov, pi)
        mu, cov, pi = maximization(datapoint, gamma)
        likelihoodarray.append(loglikelihood)

    debug("{sep} Result {sep}".format(sep="-" * 20))
    debug("mu:", mu, "cov:", cov, "pi:", pi, sep="\n")
    return mu, cov, pi, likelihoodarray


if __name__ == "__main__":
    DEBUG = True  # debugging mode flag

    # Load data from .mat file as array-like data
    mat = spio.loadmat("mixtureData.mat")
    Y = mat['Y']
    print(Y.shape)
    matY = np.matrix(Y, copy=True)

    # the main entry of EM algorithm for mixture model, to change the k
    mu, cov, pi, loglikelihoods = MM_EM(matY, 3, 100)

    # get the final gamma for clustering
    N = Y.shape[0]
    gamma, likelihood = Expectation(matY, mu, cov, pi)
    category = gamma.argmax(axis=1).flatten().tolist()[0]
    # Separating all data point into k clusters and store them
    class1 = np.array([Y[i] for i in range(N) if category[i] == 0])
    class2 = np.array([Y[i] for i in range(N) if category[i] == 1])
    class3 = np.array([Y[i] for i in range(N) if category[i] == 2])

    # Plot results
    plt.figure()
    #plt.subplot(1, 2, 1)
    plt.plot(class1[:, 0], class1[:, 1], 'rs')
    plt.plot(class2[:, 0], class2[:, 1], 'bo')
    plt.plot(class3[:, 0], class3[:, 1], 'go')
    plt.legend(loc="best")
    plt.title("Mixture Model Clustering By EM Algorithm")
    plt.show()

    plt.figure()
    #plt.subplot(1, 2, 2)
    plt.plot(loglikelihoods)
    plt.title("Log likelihood")
    plt.show()
