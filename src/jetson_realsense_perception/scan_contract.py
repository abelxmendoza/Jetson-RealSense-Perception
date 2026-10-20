"""Validation for portable environment package v1; no ROS or Open3D needed."""
import json
import math
from pathlib import Path
import re
import numpy as np
from .depth_pipeline import CameraModel
from .scan_mapping import validate_pose


class ScanContractError(ValueError):
    pass


def package_file(root, filename):
    if not isinstance(filename,str) or not filename or Path(filename).is_absolute():
        raise ScanContractError('asset path must be a nonempty relative path')
    root=Path(root).resolve()
    path=(root/filename).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ScanContractError(f'asset missing or outside package: {filename}')
    return path


def read_pgm(path):
    """Read 8-bit binary PGM, retaining the exact first pixel (including whitespace)."""
    data=Path(path).read_bytes();pos=0;tokens=[]
    while len(tokens)<4:
        while pos<len(data) and data[pos] in b' \t\r\n': pos+=1
        if pos<len(data) and data[pos]==35:
            end=data.find(b'\n',pos)
            if end<0: raise ScanContractError('unterminated PGM comment')
            pos=end+1;continue
        match=re.match(rb'[^\s#]+',data[pos:])
        if not match: raise ScanContractError('invalid PGM header')
        tokens.append(match.group());pos+=len(match.group())
    if tokens[0]!=b'P5' or tokens[3]!=b'255': raise ScanContractError('requires 8-bit P5 PGM')
    try: w,h=int(tokens[1]),int(tokens[2])
    except ValueError as exc: raise ScanContractError('invalid PGM dimensions') from exc
    if w<1 or h<1 or pos>=len(data) or data[pos] not in b' \t\r\n': raise ScanContractError('invalid PGM header separator')
    pos+=2 if data[pos:pos+2]==b'\r\n' else 1
    if len(data)-pos!=w*h: raise ScanContractError('PGM payload size does not match dimensions')
    return np.frombuffer(data[pos:],dtype=np.uint8).reshape(h,w)


def _json(path):
    try:
        return json.loads(Path(path).read_text(),parse_constant=lambda s: (_ for _ in ()).throw(ValueError(f'non-finite JSON: {s}')))
    except (OSError,ValueError) as exc: raise ScanContractError(f'invalid JSON: {path}: {exc}') from exc


def validate_scan(root):
    root=Path(root)
    m=_json(root/'manifest.json')
    if not isinstance(m,dict): raise ScanContractError('manifest must be an object')
    expected={'package_type':'perception_scan','schema_version':1,'units':'metres','frame':'map','axes':{'x':'forward','y':'left','z':'up'}}
    for key,value in expected.items():
        if m.get(key)!=value or (key=='schema_version' and type(m.get(key)) is not int):
            raise ScanContractError(f'unsupported or missing {key}')
    if m.get('source') not in ('synthetic','hardware','dataset'): raise ScanContractError('unsupported source')
    if m.get('pose_source') not in ('ground_truth','external','rtabmap'): raise ScanContractError('unsupported pose_source')
    try:
        transform=validate_pose(m.get('T_realmforge_map'))
    except (ValueError,TypeError) as exc: raise ScanContractError('invalid T_realmforge_map') from exc
    if not np.allclose(transform,[[0,-1,0,0],[0,0,1,0],[-1,0,0,0],[0,0,0,1]]):
        raise ScanContractError('unsupported RealmForge transform for v1')
    files=m.get('files')
    if not isinstance(files,dict) or not {'point_cloud','occupancy'}<=files.keys(): raise ScanContractError('missing point_cloud or occupancy asset')
    paths={role:package_file(root,name) for role,name in files.items()}
    if paths['point_cloud'].suffix.lower()!='.ply': raise ScanContractError('point_cloud must be PLY')
    # Read the map image reference from the deliberately small supported YAML subset.
    text=paths['occupancy'].read_text()
    def field(name):
        matches=re.findall(r'^'+name+r'\s*:\s*(.*?)\s*$',text,re.M)
        if len(matches)!=1: raise ScanContractError(f'map YAML needs one {name}')
        return matches[0]
    image_name=field('image').strip('\"\'')
    # Image path is relative to the YAML, but still must stay in the package.
    image=package_file(root,str(paths['occupancy'].parent.relative_to(root.resolve())/image_name))
    pixels=read_pgm(image)
    try:
        resolution=float(field('resolution'));origin=json.loads(field('origin'))
    except ValueError as exc: raise ScanContractError('invalid occupancy resolution/origin') from exc
    if not math.isfinite(resolution) or resolution<=0 or not isinstance(origin,list) or len(origin)!=3 or not all(type(v) in (int,float) and math.isfinite(v) for v in origin): raise ScanContractError('invalid occupancy geometry')
    if origin[2]!=0: raise ScanContractError('rotated occupancy origins are not supported in v1')
    if not np.isin(pixels,[0,205,254]).all(): raise ScanContractError('unsupported occupancy pixel values')
    if field('negate')!='0' or float(field('occupied_thresh'))!=.65 or float(field('free_thresh'))!=.196:
        raise ScanContractError('unsupported map occupancy thresholds')
    info=m.get('occupancy')
    if info is not None:
        if not isinstance(info,dict) or info.get('resolution_m')!=resolution or info.get('origin_xy')!=origin[:2] or info.get('unknown_preserved') is not True:
            raise ScanContractError('manifest occupancy metadata disagrees with map')
    if 'depth_sequence' in paths:
        if not {'calibration','trajectory'}<=paths.keys(): raise ScanContractError('posed depth requires calibration and trajectory')
        try:
            camera=CameraModel(**_json(paths['calibration']))
            trajectory=_json(paths['trajectory'])
            with np.load(paths['depth_sequence'],allow_pickle=False) as data:
                depth,poses,times=data['depth_m'],data['T_map_camera'],data['timestamp_s']
                n=len(depth)
                if n<1 or depth.shape!=(n,camera.height,camera.width) or poses.shape!=(n,4,4) or times.shape!=(n,): raise ValueError('array shapes disagree')
                if not np.isfinite(depth).all() or (depth<0).any(): raise ValueError('depth must be finite and nonnegative')
                if not np.isfinite(times).all() or (times<0).any() or (np.diff(times)<=0).any(): raise ValueError('timestamps must increase')
                if not isinstance(trajectory,list) or len(trajectory)!=n or m.get('frames')!=n: raise ValueError('frame counts disagree')
                for i,pose in enumerate(poses):
                    validate_pose(pose)
                    if not np.allclose(pose,trajectory[i]['T_map_camera']) or times[i]!=trajectory[i]['timestamp_s']: raise ValueError('trajectory disagrees with depth archive')
        except (ValueError,TypeError,KeyError,OSError) as exc: raise ScanContractError(f'invalid posed depth: {exc}') from exc
    return m
