import numpy as np
import lmfit
from quantify_core.analysis.fitting_models import ExpDecayModel

class T1Analysis():
    def  __init__(self,qubit_dataset):
        self.dataset = qubit_dataset

    def model_fit(self):
        model = ExpDecayModel()
        
        self.magnitudes = self.dataset.y0.values
        delays = self.dataset.x0.values

        guess = model.guess(data=self.magnitudes, delay=delays)

        fit_result = model.fit(self.magnitudes, params=guess, t=delays)
        
        self.fit_delays = np.linspace( delays[0], delays[-1], 400)
        fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_delays})
        self.dataset['fit_delays'] = self.fit_delays
        self.dataset['fit_y'] = ('fit_delays',fit_y)
        return fit_result.params['tau'].value

    def plotter(self,ax):
    	
        ax.plot( self.dataset['fit_delays'].values , self.dataset['fit_y'].values,'r-',lw=3.0)
        ax.plot( self.dataset.x0.values, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'T1 experiment for {self.dataset.x0.long_name}')
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('|S21| (V)')
        
        ax.grid()
 