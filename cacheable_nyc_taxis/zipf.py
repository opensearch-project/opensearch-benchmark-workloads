# Contains helper functions used for drawing from the Zipf distribution. 

def H(i, H_list): 
    # compute the harmonic number H_n,m = sum over i from 1 to n of (1 / i^m)
    return H_list[i-1]

def precompute_H(n, m): 
    # compute the harmonic number H_n,m = sum over i from 1 to n of (1 / i^m), for all values j = 1 through n
    H_list = [1]
    for j in range(2, n+1): 
        H_list.append(H_list[-1] + 1 / (j ** m))
    return H_list

def zipf_cdf_inverse(u, H_list): 
    # To map a uniformly distributed u from [0, 1] to some probability distribution we plug it into its inverse CDF.
    # As the zipf cdf is discontinuous there is no real inverse but we can use a modified version of this solution: 
    # https://math.stackexchange.com/questions/53671/how-to-calculate-the-inverse-cdf-for-the-zipf-distribution
    # Precompute all values H_i,alpha for a fixed alpha and pass in as H_list
    if (u < 0 or u >= 1): 
        raise Exception("Input u must have 0 <= u < 1")
    n = len(H_list)
    candidate_return = 1
    denominator = H(n, H_list)
    numerator = 0
    while candidate_return < n: 
        numerator = H(candidate_return, H_list)
        if u < numerator / denominator: 
            return candidate_return
        candidate_return += 1
    return n