import dataclasses
from math import sqrt

import numpy as np
from scipy.optimize import root
from typing import Tuple, Optional, List

@dataclasses.dataclass()
class EllipseFitter:

    @staticmethod
    def fit(points: np.ndarray) -> Tuple[bool, Optional[List[float]],  Optional[List[float]], Optional[float]]:
        """Fit an ellipse to points
        Args:
            points (np.ndarray): Points to fit

        Returns:
            EllipseFitter: Result of fitting

        """

        x: np.ndarray = points[:, 0]
        y: np.ndarray = points[:, 1]
        z: np.ndarray = points[:, 2]

        # Averages
        x_avr, y_avr, z_avr = x.mean(), y.mean(), z.mean()

        xx_avr, yy_avr, zz_avr = (x ** 2).mean(), (y ** 2).mean(), (z ** 2).mean()
        xy_avr, xz_avr, yz_avr = np.dot(x, y).mean(), np.dot(x, z).mean(), np.dot(y, z).mean()

        xxx_avr, xxy_avr, xxz_avr = (x ** 3).mean(), (x ** 2 * y).mean(), (x ** 2 * z).mean()
        xyy_avr, xzz_avr, yyy_avr = (x * y ** 2).mean(), (x * z ** 2).mean(), (y ** 3).mean()
        yyz_avr, yzz_avr, zzz_avr = (y ** 2 * z).mean(), (y * z ** 2).mean(), (z ** 3).mean()

        yyyy_avr, zzzz_avr, xxyy_avr, xxzz_avr, yyzz_avr = (y ** 4).mean(), (z ** 4).mean(), (x ** 2 * y ** 2).mean(), (x ** 2 * z ** 2).mean(), (y ** 2 * z ** 2).mean()

        # Coefficients of the characteristic polynomial
        A_Matrix = np.array([[yyyy_avr, yyzz_avr, xyy_avr, yyy_avr, yyz_avr, yy_avr],
                             [yyzz_avr, zzzz_avr, xzz_avr, yzz_avr, zzz_avr, zz_avr],
                             [xyy_avr, xzz_avr, xx_avr, xy_avr, xz_avr, x_avr],
                             [yyy_avr, yzz_avr, xy_avr, yy_avr, yz_avr, y_avr],
                             [yyz_avr, zzz_avr, xz_avr, yz_avr, zz_avr, z_avr],
                             [yy_avr, zz_avr, x_avr, y_avr, z_avr, 1]])
        # Constant vector at right hand side
        B_Matrix = np.array([[-xxyy_avr], [-xxzz_avr], [-xxx_avr], [-xxy_avr], [-xxz_avr], [-xx_avr]])

        # Solve A @ result = B
        result: np.ndarray = root(lambda _x: np.squeeze(np.matmul(A_Matrix, np.expand_dims(_x, -1)) - B_Matrix), np.zeros(shape=(6,))).x

        x0 = -result[2] / 2  # X coordinate of the center
        y0 = -result[3] / (2 * result[0])  # Y coordinate of the center
        z0 = -result[4] / (2 * result[1])  # Z coordinate of the center

        # Get the length of the semi-major axis
        try:
            # X-axis length
            A = sqrt(x0 * x0 + result[0] * y0 * y0 + result[1] * z0 * z0 - result[5])
            # Y-axis length
            B = A / sqrt(result[0])
            # Z-axis length
            C = A / sqrt(result[1])

            ret = True
            pos = [x0, y0, z0]
            length = [A, B, C]
            score = np.sum(np.array(pos) ** 2) + np.std(length)
            return ret, pos, length, score

        except ValueError as _:
            return False, None, None, None
