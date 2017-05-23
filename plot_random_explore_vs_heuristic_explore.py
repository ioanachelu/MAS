import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

x = [97, 18, 168, 18, 17]

y = [268, 99, 80, 71, 128]

mean_x = np.mean(x)
mean_y = np.mean(y)

print("Random search average time on test 1 {}".format(mean_y))
print("Heuristic search average time on test 1 {}".format(mean_x))

# Random search average time on test 1 129.2
# Heuristic search average time on test 1 63.6

