#!/usr/bin/env python3
"""Linux desktop/headless simulated RGB-D perception; optional RGB-only webcam."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from jetson_realsense_perception.depth_pipeline import SimulatedCamera, process_depth


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--frames', type=int, default=240)
    parser.add_argument('--output', type=Path, help='new output directory for JSONL, calibration, final depth and points')
    parser.add_argument('--webcam', type=int, help='optional webcam device index; RGB preview only, never depth')
    args = parser.parse_args()
    if args.frames < 1:
        parser.error('frames must be positive')
    if args.headless and args.webcam is not None:
        parser.error('webcam preview requires GUI mode')
    cv2 = None
    if not args.headless:
        import os
        if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
            parser.error('no desktop display; use --headless')
        import cv2
    camera = SimulatedCamera()
    handle = None
    webcam = None
    if args.output:
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output/'camera.json').write_text(json.dumps({'intrinsics': asdict(camera.camera), 'frame_id': 'camera_optical_frame', 'source': 'synthetic', 'depth_units': 'metres', 'depth_convention': 'axial z'}, indent=2))
        handle = (args.output/'recording.jsonl').open('w')
        handle.write(json.dumps({'record_type':'metadata','schema_version':1,'source':'synthetic','name':'simulated room'})+'\n')
    manual_distance = None
    manual_fault = None
    try:
        if args.webcam is not None:
            webcam = cv2.VideoCapture(args.webcam)
            if not webcam.isOpened():
                raise RuntimeError('webcam could not open; omit --webcam to run simulation alone')
        for i in range(args.frames):
            t = i/15
            # Repeating approach/retreat followed by invalid-depth, freeze, disconnect.
            phase = i % 240
            fault = 'dropout' if 120 <= phase < 150 else 'frozen' if 150 <= phase < 180 else 'disconnect' if 180 <= phase < 210 else 'none'
            distance = 1.7 + 1.1*np.cos(t*.9)
            if manual_distance is not None:
                distance = manual_distance
            if manual_fault is not None:
                fault = manual_fault
            frame = camera.capture(t, distance, fault)
            sample, evaluation, points = process_depth(frame, t)
            if handle:
                handle.write(json.dumps({'record_type':'sample','sequence':i,**sample})+'\n')
            if i % 15 == 0:
                print(f'{t:5.1f}s {evaluation.status:12} distance={sample["nearest_distance_m"]:.2f}m age={sample["data_age_ms"]:.0f}ms fault={fault}', flush=True)
            if cv2 is not None:
                image = cv2.applyColorMap(np.uint8(np.clip(frame.depth_m/6,0,1)*255), cv2.COLORMAP_TURBO)
                image = cv2.resize(image,(640,480),interpolation=cv2.INTER_NEAREST)
                cv2.rectangle(image,(640//3,480//3),(2*640//3,2*480//3),(255,255,255),2)
                cv2.putText(image,f'SYNTHETIC {evaluation.status} {sample["nearest_distance_m"]:.2f} m',(12,25),cv2.FONT_HERSHEY_SIMPLEX,.65,(255,255,255),2)
                local_map = np.zeros((480,400,3),dtype=np.uint8)
                x = ((points[:,0]+3)/6*399).astype(int)
                y = (479-points[:,2]/6*479).astype(int)
                keep = (x>=0)&(x<400)&(y>=0)&(y<480)
                local_map[y[keep],x[keep]]=(0,220,255)
                cv2.circle(local_map,(200,479),6,(255,255,255),-1)
                cv2.putText(local_map,'LOCAL MAP: 6m x 6m',(8,25),0,.55,(255,255,255),1)
                cv2.imshow('Simulated depth + camera-relative obstacles',np.hstack((image,local_map)))
                if webcam is not None:
                    ok, rgb = webcam.read()
                    if ok:
                        cv2.putText(rgb,'REAL WEBCAM: RGB ONLY / NO METRIC DEPTH',(10,30),0,.6,(0,255,255),2)
                        cv2.imshow('Laptop camera capture test',rgb)
                    else:
                        print('Webcam frame unavailable; continuing depth simulation',flush=True)
                key = cv2.waitKey(1) & 255
                if key in (27, ord('q')):
                    break
                if key in (ord('w'), ord('s')):
                    manual_distance = float(np.clip(distance + (-.15 if key == ord('w') else .15), .3, 4.5))
                if key in (ord('0'), ord('1'), ord('2'), ord('3')):
                    manual_fault = {'0':'none', '1':'dropout', '2':'frozen', '3':'disconnect'}[chr(key)]
                if key == ord('a'):
                    manual_distance = manual_fault = None
                time.sleep(1/15)
        if args.output:
            np.savez_compressed(args.output/'last_frame.npz',depth_m=frame.depth_m,points_optical_m=points,timestamp_s=frame.timestamp_s)
    finally:
        if handle: handle.close()
        if webcam is not None: webcam.release()
        if cv2 is not None: cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
