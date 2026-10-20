"""Shared scan exports: world-frame points, observed occupancy, and mesh.

Map coordinates are right-handed x forward, y left, z up, in metres.
Open3D is optional until mesh reconstruction is requested.
"""
import json
from pathlib import Path
import numpy as np
from .depth_pipeline import CameraModel, rays

# Optical (right, down, forward) -> map (forward, left, up).
OPTICAL_TO_MAP = np.array([[0.,0.,1.],[-1.,0.,0.],[0.,-1.,0.]])


def validate_pose(pose):
    pose = np.asarray(pose, dtype=float)
    if pose.shape != (4,4) or not np.isfinite(pose).all():
        raise ValueError('pose must be a finite 4x4 camera-to-map transform')
    if not np.allclose(pose[3], [0,0,0,1]) or not np.allclose(pose[:3,:3].T @ pose[:3,:3], np.eye(3), atol=1e-5) or not np.isclose(np.linalg.det(pose[:3,:3]),1):
        raise ValueError('pose must be a rigid right-handed transform')
    return pose


def room_frame(camera, pose):
    """Raycast bounded room and static box, using ground-truth poses only."""
    pose = validate_pose(pose)
    directions = rays(camera) @ pose[:3,:3].T
    origin = pose[:3,3]
    shape = directions.shape[:2]
    depth = np.full(shape, np.inf)
    for axis, plane in ((0,-3.),(0,3.),(1,-3.),(1,3.),(2,0.),(2,2.5)):
        hit = np.divide(plane-origin[axis], directions[...,axis], out=np.full(shape,np.inf), where=directions[...,axis]!=0)
        depth = np.minimum(depth, np.where(hit>0,hit,np.inf))
    near, far = np.full(shape,-np.inf), np.full(shape,np.inf)
    for axis, lo, hi in ((0,.5,1.2),(1,-.5,.5),(2,0.,1.2)):
        d = directions[...,axis]
        a = np.divide(lo-origin[axis],d,out=np.full(shape,-np.inf),where=d!=0)
        b = np.divide(hi-origin[axis],d,out=np.full(shape,np.inf),where=d!=0)
        parallel_outside = (d==0) & ((origin[axis]<lo) | (origin[axis]>hi))
        near = np.maximum(near,np.minimum(a,b))
        far = np.minimum(far,np.where(parallel_outside,-np.inf,np.maximum(a,b)))
    depth=np.minimum(depth,np.where((near>0)&(far>=near),near,np.inf))
    return np.where(np.isfinite(depth),depth,0).astype(np.float32)


class ScanBuilder:
    def __init__(self, camera=CameraModel(), resolution=.1, bounds=(-3.5,-3.5,3.5,3.5)):
        if not np.isfinite(resolution) or resolution<=0:
            raise ValueError('resolution must be positive and finite')
        if len(bounds)!=4 or not np.isfinite(bounds).all() or bounds[2]<=bounds[0] or bounds[3]<=bounds[1]:
            raise ValueError('bounds must be increasing finite xmin,ymin,xmax,ymax')
        self.camera,self.resolution,self.bounds=camera,resolution,bounds
        self.grid=np.full((int(np.ceil((bounds[3]-bounds[1])/resolution)),int(np.ceil((bounds[2]-bounds[0])/resolution))),-1,dtype=np.int8)
        self.points=[]
        self.poses=[]
        self.depths=[]

    def add(self, depth, pose, timestamp_s):
        pose=validate_pose(pose)
        depth=np.asarray(depth,dtype=np.float32)
        if depth.shape!=(self.camera.height,self.camera.width):
            raise ValueError('depth shape does not match camera')
        if not np.isfinite(timestamp_s) or timestamp_s<0 or (self.poses and timestamp_s<=self.poses[-1]['timestamp_s']):
            raise ValueError('timestamps must be finite, nonnegative, and increasing')
        valid=np.isfinite(depth)&(depth>0)&(depth<=10)
        clean=np.where(valid,depth,0)
        optical=(rays(self.camera)*clean[...,None])[valid]
        world=optical@pose[:3,:3].T+pose[:3,3]
        self.points.append(world)
        self.depths.append(clean.copy())
        self.poses.append({'timestamp_s':float(timestamp_s),'T_map_camera':pose.tolist()})
        # Height slice for rover obstacles; unobserved cells remain unknown.
        obstacles=world[(world[:,2]>.15)&(world[:,2]<1.5)]
        origin=pose[:2,3]
        for endpoint in obstacles[::3]:
            length=np.linalg.norm(endpoint[:2]-origin)
            line=np.linspace(origin,endpoint[:2],max(2,int(length/self.resolution*2)+1))
            cells=np.floor((line-np.array(self.bounds[:2]))/self.resolution).astype(int)
            inside=(cells[:,0]>=0)&(cells[:,0]<self.grid.shape[1])&(cells[:,1]>=0)&(cells[:,1]<self.grid.shape[0])
            free=cells[:-1][inside[:-1]]
            # Occupied evidence wins over free rays; static-scene export only.
            # Only near-horizontal rays establish 2D free space. Rays over
            # furniture must not clear the furniture footprint underneath.
            if abs(endpoint[2]-pose[2,3]) <= .08:
                for x,y in free:
                    if self.grid[y,x]!=100: self.grid[y,x]=0
            if inside[-1]: self.grid[cells[-1,1],cells[-1,0]]=100

    def export(self, output, source='synthetic', mesh=False):
        if source not in ('synthetic','hardware','dataset'):
            raise ValueError('unsupported source')
        if not self.points: raise ValueError('scan has no frames')
        output=Path(output)
        output.mkdir(parents=True,exist_ok=False)
        points=np.concatenate(self.points)
        with (output/'cloud.ply').open('w') as f:
            f.write(f'ply\nformat ascii 1.0\nelement vertex {len(points)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n')
            np.savetxt(f,points,fmt='%.5f')
        # ROS map convention: image top row corresponds to largest map y.
        pixels=np.where(self.grid==100,0,np.where(self.grid==0,254,205)).astype(np.uint8)
        with (output/'map.pgm').open('wb') as f:
            f.write(f'P5\n{pixels.shape[1]} {pixels.shape[0]}\n255\n'.encode()); f.write(pixels[::-1].tobytes())
        (output/'map.yaml').write_text(f'image: map.pgm\nresolution: {self.resolution}\norigin: [{self.bounds[0]}, {self.bounds[1]}, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
        (output/'poses.json').write_text(json.dumps(self.poses,indent=2))
        np.savez_compressed(output/'rgbd.npz',depth_m=np.stack(self.depths),T_map_camera=np.array([p['T_map_camera'] for p in self.poses]),timestamp_s=np.array([p['timestamp_s'] for p in self.poses]))
        (output/'camera.json').write_text(json.dumps(vars(self.camera),indent=2))
        files={'point_cloud':'cloud.ply','occupancy':'map.yaml','trajectory':'poses.json','depth_sequence':'rgbd.npz','calibration':'camera.json'}
        if mesh:
            import open3d as o3d
            volume=o3d.pipelines.integration.ScalableTSDFVolume(voxel_length=.06,sdf_trunc=.18,color_type=o3d.pipelines.integration.TSDFVolumeColorType.NoColor)
            c=self.camera
            intrinsic=o3d.camera.PinholeCameraIntrinsic(c.width,c.height,c.fx,c.fy,c.cx,c.cy)
            for depth,pose in zip(self.depths,self.poses):
                rgbd=o3d.geometry.RGBDImage.create_from_color_and_depth(o3d.geometry.Image(np.zeros((c.height,c.width,3),dtype=np.uint8)),o3d.geometry.Image(depth),depth_scale=1.,depth_trunc=10.,convert_rgb_to_intensity=False)
                volume.integrate(rgbd,intrinsic,np.linalg.inv(pose['T_map_camera']))
            surface=volume.extract_triangle_mesh();surface.compute_vertex_normals()
            if not len(surface.triangles): raise ValueError('reconstruction produced no mesh')
            if not o3d.io.write_triangle_mesh(str(output/'mesh.obj'),surface): raise OSError('mesh export failed')
            files['mesh']='mesh.obj'
        manifest={'schema_version':1,'package_type':'perception_scan','source':source,'pose_source':'ground_truth' if source=='synthetic' else 'external','units':'metres','frame':'map','axes':{'x':'forward','y':'left','z':'up'},'T_realmforge_map':[[0,-1,0,0],[0,0,1,0],[-1,0,0,0],[0,0,0,1]],'files':files,'frames':len(self.poses),'mapping':'known-pose fusion; not SLAM','occupancy':{'resolution_m':self.resolution,'origin_xy':list(self.bounds[:2]),'height_band_m':[.15,1.5],'unknown_preserved':True},'limitations':['static geometry','no robot footprint inflation','no localization or navigation validation','no inferred object semantics']}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
        from .scan_contract import validate_scan
        validate_scan(output)
        return manifest
