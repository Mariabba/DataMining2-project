import matrixprofile as mp
from matplotlib import pyplot as plt

from music import MusicDB

data = MusicDB()

rock = data.df.loc[data.feat["genre"] == "Rock"]
rock_mean = rock.mean(axis=0)
rock_mean.plot()
plt.title("Rock Mean")
plt.show()

"""
# approssimazione con sax

sax = SymbolicAggregateApproximation(n_segments=155, alphabet_size_avg=10)
X1 = sax.fit_transform(rock_mean.values.reshape(1,-1))
X = pd.DataFrame(np.squeeze(X1))

X.plot()
plt.title("Rock Mean SAX")
plt.show()
"""

vals = rock_mean.values
plt.figure(figsize=(50, 50))
profile, figures = mp.analyze(vals)
plt.show()
