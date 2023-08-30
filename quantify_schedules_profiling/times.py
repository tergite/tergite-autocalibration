import numpy
import matplotlib.pyplot as plt

comp_times = [1.50, 3.23, 5.05, 7.13, 9.11,]

qubits = numpy.arange(2,11,2)


plt.plot(qubits, comp_times,'bo')
plt.xlabel('number of qubits')
plt.ylabel('complilation time in seconds')
plt.show()
