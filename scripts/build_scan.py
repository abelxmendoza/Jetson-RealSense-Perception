#!/usr/bin/env python3
"""Build a shared scan package from simulated depth or calibrated posed depth NPZ."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jetson_realsense_perception.depth_pipeline import CameraModel
from jetson_realsense_perception.scan_mapping import ScanBuilder, OPTICAL_TO_MAP, room_frame


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path,help='new package directory')
    parser.add_argument('--frames',type=int,default=36)
    parser.add_argument('--mesh',action='store_true',help='reconstruct mesh using Open3D')
    parser.add_argument('--input-npz',type=Path,help='depth_m[N,H,W], T_map_camera[N,4,4], timestamp_s[N]')
    parser.add_argument('--camera-json',type=Path,help='CameraModel intrinsics for input NPZ')
    parser.add_argument('--source',choices=['dataset','hardware'],help='required for external data')
    args=parser.parse_args()
    if args.output.exists(): parser.error('output already exists; choose a new directory')
    if args.input_npz:
        if not args.camera_json or not args.source: parser.error('external input requires --camera-json and --source')
        camera=CameraModel(**json.loads(args.camera_json.read_text()))
        builder=ScanBuilder(camera)
        with np.load(args.input_npz,allow_pickle=False) as data:
            depths,poses,times=data['depth_m'],data['T_map_camera'],data['timestamp_s']
            if depths.ndim!=3 or poses.shape!=(len(depths),4,4) or times.shape!=(len(depths),):
                parser.error('invalid depth/pose/time array shapes')
            for depth,pose,t in zip(depths,poses,times): builder.add(depth,pose,float(t))
        source=args.source
    else:
        if args.frames<4: parser.error('simulation requires at least 4 frames')
        if args.source or args.camera_json: parser.error('source/calibration options require --input-npz')
        builder=ScanBuilder()
        for i,angle in enumerate(np.linspace(0,2*np.pi,args.frames,endpoint=False)):
            # Orbit the box at 2 m radius and look inward; camera is 1 m high.
            yaw=angle+np.pi
            rot=np.array([[np.cos(yaw),-np.sin(yaw),0],[np.sin(yaw),np.cos(yaw),0],[0,0,1]])
            pose=np.eye(4);pose[:3,:3]=rot@OPTICAL_TO_MAP
            pose[:3,3]=[2*np.cos(angle),2*np.sin(angle),1.]
            builder.add(room_frame(builder.camera,pose),pose,i/15)
        source='synthetic'
    manifest=builder.export(args.output,source,mesh=args.mesh)
    print(json.dumps({'output':str(args.output),'source':source,'frames':manifest['frames'],'files':manifest['files']},indent=2))


if __name__=='__main__': main()
