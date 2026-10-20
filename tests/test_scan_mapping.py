import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from jetson_realsense_perception.depth_pipeline import CameraModel
from jetson_realsense_perception.scan_mapping import ScanBuilder, OPTICAL_TO_MAP, room_frame, validate_pose

class ScanMappingTests(unittest.TestCase):
    def test_known_world_surface_and_transform(self):
        camera=CameraModel(3,3,2,2,1,1)
        pose=np.eye(4);pose[:3,:3]=OPTICAL_TO_MAP;pose[:3,3]=[-2,0,1]
        depth=room_frame(camera,pose)
        self.assertAlmostEqual(depth[1,1],2.5)
        builder=ScanBuilder(camera);builder.add(depth,pose,0)
        np.testing.assert_allclose(builder.points[0][4],[.5,0,1])

    def test_rays_preserve_unknown_and_mark_obstacles(self):
        camera=CameraModel(3,3,2,2,1,1)
        pose=np.eye(4);pose[:3,:3]=OPTICAL_TO_MAP;pose[2,3]=1
        builder=ScanBuilder(camera)
        builder.add(np.full((3,3),2,dtype=np.float32),pose,0)
        self.assertTrue((builder.grid==-1).any())
        self.assertTrue((builder.grid==0).any())
        self.assertTrue((builder.grid==100).any())

    def test_bad_poses_and_nonincreasing_time_rejected(self):
        with self.assertRaises(ValueError): validate_pose(np.zeros((4,4)))
        camera=CameraModel(3,3,2,2,1,1)
        builder=ScanBuilder(camera);builder.add(np.ones((3,3)),np.eye(4),1)
        with self.assertRaises(ValueError): builder.add(np.ones((3,3)),np.eye(4),1)

    def test_exports_relocatable_map_and_pose_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'scan'
            result=subprocess.run([sys.executable,str(ROOT/'scripts/build_scan.py'),str(output),'--frames','4'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['source'],'synthetic')
            for filename in manifest['files'].values(): self.assertTrue((output/filename).is_file())
            self.assertIn('image: map.pgm',(output/'map.yaml').read_text())
            with np.load(output/'rgbd.npz') as data: self.assertEqual(data['T_map_camera'].shape,(4,4,4))
            duplicate=subprocess.run([sys.executable,str(ROOT/'scripts/build_scan.py'),str(output)],capture_output=True)
            self.assertNotEqual(duplicate.returncode,0)
