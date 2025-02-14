import multiprocessing

import numpy as np
import pandas as pd
from rich import print
from rich.progress import BarColumn, Progress, TimeRemainingColumn
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.preprocessing import TimeSeriesScalerMeanVariance

from music import MusicDB


def do_sax_knn(params):
    # unpack
    Xi, yi, segments, symbols, k = params

    # Make sax
    sax = SymbolicAggregateApproximation(n_segments=segments, alphabet_size_avg=symbols)
    ts_sax = sax.fit_transform(Xi)

    x_train, x_test, y_train, y_test = train_test_split(
        ts_sax, yi, test_size=0.2, random_state=100, stratify=yi
    )
    kn = KNeighborsClassifier(n_neighbors=k, p=1, weights="distance")
    kn.fit(np.squeeze(x_train), y_train)
    kn_d = KNeighborsClassifier(n_neighbors=k, p=2, weights="distance")
    kn_d.fit(np.squeeze(x_train), y_train)

    y_pred = kn.predict(np.squeeze(x_test))
    y_pred_manh = kn_d.predict(np.squeeze(x_test))

    return (
        segments,
        symbols,
        k,
        round(accuracy_score(y_test, y_pred), 4),
        round(accuracy_score(y_test, y_pred_manh), 4),
    )


if __name__ == "__main__":
    # KNN with SAX, grid search, multiprocessing
    segments = 1000
    symbols = 100
    k = 30

    musi = MusicDB()
    # Rescale - but why?
    scaler = TimeSeriesScalerMeanVariance()  # Rescale time series
    x = scaler.fit_transform(musi.df)
    x = pd.DataFrame(x.reshape(musi.df.values.shape[0], musi.df.values.shape[1]))
    x.index = musi.df.index
    y = musi.feat["enc_genre"]

    # build param collection
    param_collection = []
    for seg in range(5, segments, 25):
        for symb in range(5, symbols, 5):
            for ki in range(3, k, 2):
                param_collection.append((x, y, seg, symb, ki))

    # make results
    pl_results = []
    event_steps = [int(len(param_collection) * i / 1000) for i in range(1000)]
    event_steps.append(1)
    event_steps = set(event_steps)

    # make progress reporting
    progress = Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "{task.completed} of {task.total}",
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
    )

    # populate results
    with progress:
        task_id = progress.add_task("[cyan]KNN…", total=len(param_collection))
        with multiprocessing.Pool() as pool:
            for one_result in pool.imap_unordered(do_sax_knn, param_collection):
                pl_results.append(one_result)
                progress.advance(task_id)
                if int(progress._tasks[task_id].completed) in event_steps:
                    with open("data/tokens/progress.txt", "w") as f:
                        f.write(str(progress._tasks[task_id].completed))

    # make df
    dfm = pd.DataFrame(
        pl_results,
        columns=["segments", "symbols", "k", "acc euclidean", "acc manhattan"],
    )

    # output results
    print(dfm.sort_values(by="acc euclidean", ascending=False).iloc[:20, :])
    print(dfm.sort_values(by="acc manhattan", ascending=False).iloc[:20, :])
