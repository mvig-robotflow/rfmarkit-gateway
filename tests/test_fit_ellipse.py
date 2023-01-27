import numpy as np
from tcpbroker.functional import EllipseFitResult


if __name__ == '__main__':
    data = np.array([[0, 0, 2],
                     [0, 2, 0],
                     [2, 0, 0],
                     [-2, 0, 0],
                     [0, -2, 0],
                     [0, 0, -2]])
    res = EllipseFitResult()
    res.fit(data)
    if res.ret:
        print("Fit result ")
        print("xo = ", res.pos[0])
        print("yo = ", res.pos[1])
        print("zo = ", res.pos[2])
        print("A = ", res.length[0])
        print("B = ", res.length[1])
        print("C = ", res.length[2])
        print("Score = ", res.score)
