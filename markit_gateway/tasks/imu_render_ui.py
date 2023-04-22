import logging
import math
import multiprocessing as mp
import os
import random
import time
from typing import Tuple, Dict, Any, Optional

import numpy as np
import tqdm
import vtk


def init_canvas(title: str = "IMU", resolution: Tuple[int] = (960, 540)):
    # 渲染（将执行单元和背景组合在一起按照某个视角绘制）
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    interactor = vtk.vtkRenderWindowInteractor()
    renderer.SetBackground(1.0, 1.0, 1.0)

    render_window.AddRenderer(renderer)
    render_window.SetWindowName(title)
    render_window.SetSize(*resolution)
    render_window.Render()

    # 显示渲染窗口
    interactor.SetRenderWindow(render_window)
    interactor.Initialize()
    interactor.CreateRepeatingTimer(10)

    return renderer, render_window, interactor


class IMUAxisActorBundle:
    def __init__(self, path_to_model='./obj', grey: bool = False):
        self.path_to_model = os.path.join(os.path.dirname(os.path.abspath(__file__)), "obj")
        x_axis_stl_path = os.path.join(path_to_model, os.path.join(self.path_to_model, 'x.stl'))
        y_axis_stl_path = os.path.join(path_to_model, os.path.join(self.path_to_model, 'y.stl'))
        z_axis_stl_path = os.path.join(path_to_model, os.path.join(self.path_to_model, 'z.stl'))

        self.x_actor = self.add_stl_object(x_axis_stl_path)
        self.y_actor = self.add_stl_object(y_axis_stl_path)
        self.z_actor = self.add_stl_object(z_axis_stl_path)

        if not grey:
            self.x_actor.GetProperty().SetColor(1.0, 0.0, 0.0)
            self.y_actor.GetProperty().SetColor(0.0, 1.0, 0.0)
            self.z_actor.GetProperty().SetColor(0.0, 0.0, 1.0)

    @staticmethod
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


class vtkTimerCallback:
    def __init__(self, renderer, in_queue: mp.Queue = None, stop_ev: mp.Event = None):
        self.renderer = renderer
        self.in_queue = in_queue
        self.stop_ev: Optional[mp.Event] = stop_ev

        self.imu_actors: Dict[str, IMUAxisActorBundle] = {}
        self.imu_pos: Dict[str, np.ndarray] = {}  # id -> [r, p, y]
        self.imu_euler: Dict[str, np.ndarray] = {}  # id -> [x, y, z]

        self.tick_count = 0
        self.pbar = tqdm.tqdm()

        self._create_world_actor()

    def _create_world_actor(self):
        act = IMUAxisActorBundle(grey=True)
        self.renderer.AddActor(act.x_actor)
        self.renderer.AddActor(act.y_actor)
        self.renderer.AddActor(act.z_actor)
        self.imu_actors['world'] = act
        self.imu_pos['world'] = np.array([0., 0., 0.])
        self.imu_euler['world'] = np.array([0., 0., 0.])

    def _create_imu_actor(self, imu_id: str):
        act = IMUAxisActorBundle()
        self.renderer.AddActor(act.x_actor)
        self.renderer.AddActor(act.y_actor)
        self.renderer.AddActor(act.z_actor)
        self.imu_actors[imu_id] = act

        _width = 4
        _gap = 15
        x, y = len(self.imu_actors) % _width, len(self.imu_actors) // _width
        self.imu_pos[imu_id] = np.array([x * _gap, y * _gap, 0]).astype(float)

    def _decode_imu_state_dict(self, imu_dict: Dict[str, Any]):
        if imu_dict['id'] not in self.imu_actors.keys():
            self._create_imu_actor(imu_dict['id'])

        q0, q1, q2, q3 = imu_dict["quat_w"], imu_dict["quat_x"], imu_dict["quat_y"], imu_dict["quat_z"]
        roll = - math.atan2(2 * (q2 * q3 - q0 * q1), 2 * (q0 ** 2 + q3 ** 2) - 1) * 180 / math.pi
        pitch = math.asin(2 * (q1 * q3 + q0 * q2)) * 180 / math.pi
        yaw = - math.atan2(2 * (q1 * q2 - q0 * q3), 2 * (q0 ** 2 + q1 ** 2) - 1) * 180 / math.pi

        self.imu_euler[imu_dict['id']] = np.array([roll, pitch, yaw])

    def execute(self, obj, event):

        count = 0
        while self.in_queue.qsize() > 100 and count < 10:
            imu_dict = self.in_queue.get()
            self._decode_imu_state_dict(imu_dict)
            count += 1

        for actor_id, actor in self.imu_actors.items():
            actor.x_actor.SetOrientation(0, 0, 0)
            actor.x_actor.RotateWXYZ(self.imu_euler[actor_id][0], 1, 0, 0)
            actor.x_actor.RotateWXYZ(self.imu_euler[actor_id][1], 0, 1, 0)
            actor.x_actor.RotateWXYZ(self.imu_euler[actor_id][2], 0, 0, 1)
            actor.x_actor.SetPosition(self.imu_pos[actor_id][0], self.imu_pos[actor_id][1], self.imu_pos[actor_id][2])

            actor.y_actor.SetOrientation(0, 0, 0)
            actor.y_actor.RotateWXYZ(self.imu_euler[actor_id][0], 1, 0, 0)
            actor.y_actor.RotateWXYZ(self.imu_euler[actor_id][1], 0, 1, 0)
            actor.y_actor.RotateWXYZ(self.imu_euler[actor_id][2], 0, 0, 1)
            actor.y_actor.SetPosition(self.imu_pos[actor_id][0], self.imu_pos[actor_id][1], self.imu_pos[actor_id][2])

            actor.z_actor.SetOrientation(0, 0, 0)
            actor.z_actor.RotateWXYZ(self.imu_euler[actor_id][0], 1, 0, 0)
            actor.z_actor.RotateWXYZ(self.imu_euler[actor_id][1], 0, 1, 0)
            actor.z_actor.RotateWXYZ(self.imu_euler[actor_id][2], 0, 0, 1)
            actor.z_actor.SetPosition(self.imu_pos[actor_id][0], self.imu_pos[actor_id][1], self.imu_pos[actor_id][2])

        iren = obj
        iren.GetRenderWindow().Render()

        if self.stop_ev is not None:
            if self.stop_ev.is_set():
                return

        # self.tick_count += 1
        # if self.tick_count % 100 == 0 and self.tick_count != 0:
        #     self.pbar.update(100)


def keyboard_interact_task(imu_id: str, q: mp.Queue):
    while True:
        time.sleep(0.05)
        imu_data_dict = {
            "quat_w": 1 + random.random() * 0.03,
            "quat_x": 0 + random.random() * 0.03,
            "quat_y": 0 + random.random() * 0.03,
            "quat_z": 0 + random.random() * 0.03,
            "id": imu_id
        }
        q.put(imu_data_dict)


def imu_render_ui_task(stop_ev: mp.Event,
                       finish_ev: mp.Event,
                       q: mp.Queue):
    if stop_ev.is_set():
        return

    renderer, _, interactor = init_canvas()

    # Add callback
    cb = vtkTimerCallback(renderer, q)
    interactor.AddObserver('TimerEvent', cb.execute)

    try:
        interactor.Start()
    except KeyboardInterrupt as e:
        finish_ev.set()
        logging.info('keyboard interrupt')
        return
    finally:
        finish_ev.set()

    logging.info("imu_render_ui_task finished")
    finish_ev.set()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    shared_queue = mp.Queue(maxsize=100)
    stop_ev = mp.Event()
    finish_ev = mp.Event()

    keyboard_process_1 = mp.Process(None, keyboard_interact_task, "keyboard_interact_task_1",
                                    ('test1', shared_queue,))
    keyboard_process_1.start()

    render_process = mp.Process(None, imu_render_ui_task, "render_task",
                                (stop_ev, finish_ev, shared_queue,))
    render_process.start()

    time.sleep(10)

    keyboard_process_2 = mp.Process(None, keyboard_interact_task, "keyboard_interact_task_2",
                                    ('test2', shared_queue,))
    keyboard_process_2.start()

    finish_ev.wait()
    keyboard_process_2.kill()
    keyboard_process_1.kill()
    logging.info('finished')
