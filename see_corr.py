#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

# Load correlation values
corr_file = "correlation.npy"
corr = np.load(corr_file)

# Plot
plt.figure(figsize=(12,4))
plt.plot(corr)
plt.title("Correlation with Preamble")
plt.xlabel("Sample index")
plt.ylabel("Correlation magnitude")
plt.grid(True)
plt.show()