import math
import random
from typing import List

import tqdm
import vtk


class vtkTimerCallback():
    def __init__(self, actors: List[vtk.vtkActor]):
        self.actors = actors
        self.timer_count = 0
        self.transform = None
        self.pbar = tqdm.tqdm()

    def _update_transform(self):
        imu_data_dict = {
            "q0": 1 + random.random() * 0.03,
            "q1": 0 + random.random() * 0.03,
            "q2": 0 + random.random() * 0.03,
            "q3": 0 + random.random() * 0.03
        }

        q0, q1, q2, q3 = imu_data_dict["q0"], imu_data_dict["q1"], imu_data_dict["q2"], imu_data_dict["q3"]
        # roll = math.atan2(2*(q0*q3+q1*q2), 1-2*(q2**2+q3**2)) * 180 / math.pi
        # pitch = math.asin(2*(q0*q2-q3*q1)) * 180 / math.pi
        # yaw = math.atan2(2*(q0*q1+q2*q3), 1-2*(q1**2+q2**2)) * 180 / math.pi
        roll = - math.atan2(2 * (q2 * q3 - q0 * q1), 2 * (q0 ** 2 + q3 ** 2) - 1) * 180 / math.pi
        pitch = math.asin(2 * (q1 * q3 + q0 * q2)) * 180 / math.pi
        yaw = - math.atan2(2 * (q1 * q2 - q0 * q3), 2 * (q0 ** 2 + q1 ** 2) - 1) * 180 / math.pi

        self.transform = {'roll': roll, 'pitch': pitch, 'yaw': yaw}
        # print('roll: {:3f}, pitch: {:3f}, yaw: {:3f}'.format(roll, pitch, yaw))
        if self.timer_count % 100 == 0 and self.timer_count != 0:
            self.pbar.update(100)

    def execute(self, obj, event):
        self._update_transform()

        for actor in self.actors:
            actor.SetOrientation(0, 0, 0)
            actor.RotateWXYZ(self.transform['roll'], 1, 0, 0)
            actor.RotateWXYZ(self.transform['pitch'], 0, 1, 0)
            actor.RotateWXYZ(self.transform['yaw'], 0, 0, 1)

        iren = obj
        iren.GetRenderWindow().Render()
        self.timer_count += 1


def add_stl_object(filename) -> vtk.vtkActor:
    reader = vtk.vtkSTLReader()
    reader.SetFileName(filename)

    # Create a mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Create an actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor


if __name__ == '__main__':
    X_AXIS_STL_FILENAME = './obj/x.stl'
    Y_AXIS_STL_FILENAME = './obj/y.stl'
    Z_AXIS_STL_FILENAME = './obj/z.stl'

    x_actor = add_stl_object(X_AXIS_STL_FILENAME)
    y_actor = add_stl_object(Y_AXIS_STL_FILENAME)
    z_actor = add_stl_object(Z_AXIS_STL_FILENAME)

    x_actor.GetProperty().SetColor(1.0, 0.0, 0.0)
    y_actor.GetProperty().SetColor(0.0, 1.0, 0.0)
    z_actor.GetProperty().SetColor(0.0, 0.0, 1.0)

    # 4. 渲染（将执行单元和背景组合在一起按照某个视角绘制）
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    interactor = vtk.vtkRenderWindowInteractor()

    renderer.AddActor(x_actor)
    renderer.AddActor(y_actor)
    renderer.AddActor(z_actor)
    renderer.SetBackground(1.0, 1.0, 1.0)

    render_window.AddRenderer(renderer)
    render_window.SetWindowName("IMU")
    render_window.SetSize(960, 540)
    render_window.Render()

    # 5. 显示渲染窗口
    interactor.SetRenderWindow(render_window)
    interactor.Initialize()

    # 6. Add callback
    cb = vtkTimerCallback([x_actor, y_actor, z_actor])
    interactor.AddObserver('TimerEvent', cb.execute)
    interactor.CreateRepeatingTimer(10)
    interactor.Start()

    print('bye bye')
