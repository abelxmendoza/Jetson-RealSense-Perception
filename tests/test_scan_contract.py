import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from jetson_realsense_perception.depth_pipeline import CameraModel
from jetson_realsense_perception.scan_mapping import ScanBuilder, OPTICAL_TO_MAP
from jetson_realsense_perception.scan_contract import ScanContractError, package_file, read_pgm, validate_scan
from jetson_realsense_perception.scan_consumers import RoverMap, realmforge_world

class ScanContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.output=Path(self.tmp.name)/'scan'
        builder=ScanBuilder(CameraModel(3,3,2,2,1,1))
        pose=np.eye(4);pose[:3,:3]=OPTICAL_TO_MAP;pose[2,3]=1
        builder.add(np.full((3,3),2,dtype=np.float32),pose,0)
        builder.export(self.output)

    def mutate(self,key,value):
        p=self.output/'manifest.json';m=json.loads(p.read_text());m[key]=value;p.write_text(json.dumps(m))

    def test_valid_roundtrip(self):
        self.assertEqual(validate_scan(self.output)['source'],'synthetic')

    def test_reject_versions_units_and_frame(self):
        original=(self.output/'manifest.json').read_text()
        for k,v in [('schema_version',2),('schema_version',True),('units','feet'),('frame','optical')]:
            with self.subTest(k=k,v=v):
                (self.output/'manifest.json').write_text(original)
                self.mutate(k,v)
                with self.assertRaises(ScanContractError): validate_scan(self.output)

    def test_path_traversal_and_symlink_rejected(self):
        outside=Path(self.tmp.name)/'outside';outside.write_text('private')
        for name in ('../outside',str(outside)):
            with self.assertRaises(ScanContractError): package_file(self.output,name)
        (self.output/'link').symlink_to(outside)
        with self.assertRaises(ScanContractError): package_file(self.output,'link')

    def test_pose_archive_must_match_trajectory(self):
        p=self.output/'poses.json';poses=json.loads(p.read_text());poses[0]['T_map_camera'][0][3]+=1;p.write_text(json.dumps(poses))
        with self.assertRaisesRegex(ScanContractError,'trajectory disagrees'): validate_scan(self.output)

    def test_map_metadata_mismatch_rejected(self):
        m=json.loads((self.output/'manifest.json').read_text());m['occupancy']['resolution_m']=1
        self.mutate('occupancy',m['occupancy'])
        with self.assertRaisesRegex(ScanContractError,'disagrees'): validate_scan(self.output)

    def test_pgm_does_not_eat_whitespace_pixel(self):
        p=self.output/'small.pgm';p.write_bytes(b'P5\n# comment\n2 1\n255\n'+bytes([10,254]))
        np.testing.assert_array_equal(read_pgm(p),[[10,254]])

class ExperimentalConsumerTests(unittest.TestCase):
    def test_unknown_and_occupied_are_blocked(self):
        grid=np.zeros((9,9));grid[4,4]=100;grid[1,1]=-1
        rover=RoverMap(grid,1,[0,0])
        for point in ([4.5,4.5],[1.5,1.5],[-1,0]):
            with self.assertRaises(ValueError): rover.plan(point,[7.5,7.5],0)
        route=rover.plan([2.5,4.5],[6.5,4.5],0)
        for point in route:
            x,y=rover.cell(point);self.assertEqual(grid[y,x],0)
        inflated=rover.blocked(1)
        self.assertTrue(inflated[4,3])

    def test_invalid_values_cannot_wrap_to_free(self):
        with self.assertRaises(ValueError): RoverMap([[256]],1,[0,0])

    def test_realmforge_transform_and_unknown_blocker(self):
        world=realmforge_world(RoverMap([[-1,100,0]],.5,[1,2]))
        self.assertFalse(world['robotEnabled'])
        self.assertEqual(len(world['objects']),2)
        self.assertEqual(world['objects'][0]['position'],[-2.25,0,-1.25])
