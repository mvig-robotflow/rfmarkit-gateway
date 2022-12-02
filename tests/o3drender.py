import logging
import multiprocessing as mp

logging.basicConfig(level=logging.INFO)


def imu_render_ui_task(stop_ev: mp.Event, finish_ev: mp.Event, in_queue: mp.Queue):
    x = None
    try:
        while True:
            if stop_ev.is_set():
                break
            try:
                x = None
                x = in_queue.get(timeout=1)
            except Exception as e:
                pass
            if x is not None:
                print(x)
    except KeyboardInterrupt:
        logging.debug(f"imu_render_ui exitting")
        finish_ev.set()

    finish_ev.set()


import open3d as o3d
from scipy.spatial.transform import Rotation
from typing import List, Tuple


def vis_quats(quats: List[Tuple[float, float, float, float]]):
    # quants: list of tuples. should be in (w, x, y, z) format
    imu_coords = [o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.3)]
    for idx, quat in enumerate(quats):
        w, x, y, z = quat
        rot = Rotation.from_quat((x, y, z, w))

        imu_coord = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.1)
        imu_coord.translate(((idx + 1) * 0.3, 0, 0))
        imu_coord.rotate(rot.as_matrix())
        imu_coords.append(imu_coord)

    o3d.visualization.draw_geometries(imu_coords)  # Interactive


class QuatVisualizer:
    def __init__(self):
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window()
        self._world_coord = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.3)
        self.vis.add_geometry(self._world_coord)
        self._last_coords = []

    def visualize(self, quats: List[Tuple[float, float, float, float]]):
        # quants: list of tuples. should be in (w, x, y, z) format
        imu_coords = []
        for idx, quat in enumerate(quats):
            w, x, y, z = quat
            rot = Rotation.from_quat((x, y, z, w))

            imu_coord = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.1)
            imu_coord.translate(((idx + 1) * 0.3, 0, 0))
            imu_coord.rotate(rot.as_matrix())
            imu_coords.append(imu_coord)

        for imu_coord in self._last_coords:
            self.vis.remove_geometry(imu_coord, reset_bounding_box=False)  # dirty hacks...
        for imu_coord in imu_coords:
            self.vis.add_geometry(imu_coord, reset_bounding_box=False)
        self.vis.poll_events()
        self.vis.update_renderer()
        self._last_coords = imu_coords

    def close(self):
        self.vis.destroy_window()

    def __del__(self):
        self.vis.destroy_window()


if __name__ == "__main__":
    quats = [
        (0.7071, 0., 0.7071, 0.),
        (1., 0., 0., 0.),
        (0., 0., 1., 0.),
        (0.7071, 0., -0.7071, 0.),
    ]
    # A blocking example
    # vis_quats(quats)

    from tqdm import tqdm
    import copy
    import random

    # non-blocking example
    visualizer = QuatVisualizer()
    for idx in tqdm(range(1000)):
        _quats = copy.deepcopy(quats)
        random.shuffle(_quats)
        visualizer.visualize(_quats)

    visualizer.close()
