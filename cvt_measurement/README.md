# CVTMeasurement

A tool for converting measurement data from IMU.

## Install

```shell
git clone https://github.com/mvig-robotflow/rfimu-interface
cd cvt_measurement
python setup.py develop
```

## Usage

```python
# Convert imu data to npz
from cvt_measurement import convert_measurement
measurement_base_dir = "path/to/your/measurement"
result = convert_measurement(measurement_base_dir, delete_dat=False)

# Check magnetic readings
import numpy as np
from cvt_measurement import EllipseFitResult
imu_id = "some_imu_id"
points = np.concatenate([result[imu_id]["mag_x"], result[imu_id]["mag_y"], result[imu_id]["mag_z"]], axis=1)
res = EllipseFitResult()
res.fit(points)
```
