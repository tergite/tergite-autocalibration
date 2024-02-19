import matplotlib.pyplot as plt


fig, axs = plt.subplots(ncols=2,nrows=1)

# axs[0].plot([1,2,3], [1,2,3])
axs[1].plot([1,2,3], [1,2,3])
axs[0].remove()

f = plt.gcf()
grid = axs[0].get_subplotspec().get_gridspec()
subf = f.add_subfigure(grid[0])
aax = subf.subplots(2,1)
aax[0].plot([1,1,1])
aax[1].plot([2,2,2])
plt.show()
