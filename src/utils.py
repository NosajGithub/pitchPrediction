import random


def reservoir_sampling(N_population, n_samples):
    results = []
    for i, item in enumerate(N_population):
        if i < n_samples:
            results.append(item)
        else:
            k = random.randint(0, i)
            if k < n_samples:
                results[k] = item

    return results