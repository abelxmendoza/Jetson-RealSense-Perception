import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jetson_realsense_perception.depth_pipeline import CameraModel, DepthFrame, SimulatedCamera, point_cloud, process_depth

class DepthPipelineTests(unittest.TestCase):
    def test_approaching_obstacle_changes_decision(self):
        camera=SimulatedCamera()
        for distance,status in ((2.,'CLEAR'),(.7,'STOP')):
            sample,result,points=process_depth(camera.capture(0,distance),0)
            self.assertAlmostEqual(sample['nearest_distance_m'],distance,places=5)
            self.assertEqual(result.status,status)
            self.assertGreater(len(points),0)

    def test_faults_take_precedence_over_close_obstacle(self):
        for fault in ('dropout','disconnect'):
            _,result,_=process_depth(SimulatedCamera().capture(0,.7,fault),0)
            self.assertEqual(result.status,'SENSOR_FAULT')

    def test_frozen_frame_keeps_original_timestamp(self):
        camera=SimulatedCamera()
        first=camera.capture(0,2)
        frozen=camera.capture(1,2,'frozen')
        self.assertIs(first,frozen)
        sample,result,_=process_depth(frozen,1)
        self.assertEqual(sample['data_age_ms'],1000)
        self.assertEqual(result.status,'SENSOR_FAULT')

    def test_projection_has_known_optical_coordinates(self):
        model=CameraModel(3,3,1,1,1,1)
        depth=np.zeros((3,3)); depth[1,1]=2; depth[1,2]=2
        points=point_cloud(DepthFrame(depth,model,0,'synthetic'))
        np.testing.assert_allclose(points,[[0,0,2],[2,0,2]])

    def test_bad_depth_is_excluded_and_shape_checked(self):
        model=CameraModel(3,3,1,1,1,1)
        depth=np.full((3,3),np.nan)
        sample,result,points=process_depth(DepthFrame(depth,model,0,'synthetic'),0)
        self.assertEqual(result.status,'SENSOR_FAULT')
        self.assertEqual(len(points),0)
        with self.assertRaises(ValueError):
            point_cloud(DepthFrame(np.ones((2,2)),model,0,'synthetic'))
