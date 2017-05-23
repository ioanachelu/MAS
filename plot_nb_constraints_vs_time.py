import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

x = [6, 5, 4, 3, 2, 1, 0]

y = [99, 78, 39, 15, 13, 12, 8]
# best_x = np.argmin(np.asarray(y))
# best_y = np.min(np.asarray(y))

fig = plt.figure()
ax = fig.add_subplot(111)
ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))
ax.plot(x, y, 'bo', x, y, 'b')
# plt.axis..set_major_formatter(mtick.FormatStrFormatter('%.2e'))
ax.set_ylabel('Time')
ax.set_ylabel('Nb BAs')
fig.show()
fig.savefig('analysis_nb_constr_vs_time_for_test1_2_constr_for_each_ba.png')

