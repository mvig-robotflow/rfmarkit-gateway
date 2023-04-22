import numpy as np
from markit_gateway.functional import EllipseFitter


if __name__ == '__main__':
    data = np.array([[0, 0, 2],
                     [0, 2, 0],
                     [2, 0, 0],
                     [-2, 0, 0],
                     [0, -2, 0],
                     [0, 0, -2]])
    res = EllipseFitter()
    print(res.fit(data))
