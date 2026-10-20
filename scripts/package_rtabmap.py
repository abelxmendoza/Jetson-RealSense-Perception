#!/usr/bin/env python3
"""Package existing RTAB-Map exports; does not run SLAM or guess export flags."""
import argparse
import json
from pathlib import Path
import re
import shutil


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--cloud',type=Path,required=True,help='exported PLY cloud in map coordinates')
    parser.add_argument('--map-yaml',type=Path,required=True)
    parser.add_argument('--map-image',type=Path,required=True,help='PGM occupancy image referenced by YAML')
    parser.add_argument('--mesh',type=Path,help='optional standalone, untextured OBJ mesh')
    parser.add_argument('--source',choices=['hardware','dataset','synthetic'],required=True)
    args=parser.parse_args()
    for path,suffix in ((args.cloud,'.ply'),(args.map_yaml,'.yaml'),(args.map_image,'.pgm'),(args.mesh,'.obj')):
        if path is not None and (not path.is_file() or path.suffix.lower()!=suffix): parser.error(f'expected existing {suffix} file: {path}')
    text=args.map_yaml.read_text()
    if len(re.findall(r'^image\s*:',text,re.M))!=1: parser.error('map YAML requires exactly one image entry')
    if args.mesh and re.search(r'^\s*(mtllib|usemtl)\s',args.mesh.read_text(),re.M):
        parser.error('textured/material OBJ requires asset bundling; export an untextured mesh for now')
    args.output.mkdir(parents=True,exist_ok=False)
    files={'point_cloud':'cloud.ply','occupancy':'map.yaml'}
    shutil.copyfile(args.cloud,args.output/'cloud.ply')
    shutil.copyfile(args.map_image,args.output/'map.pgm')
    (args.output/'map.yaml').write_text(re.sub(r'^image\s*:.*$','image: map.pgm',text,flags=re.M))
    if args.mesh:
        shutil.copyfile(args.mesh,args.output/'mesh.obj');files['mesh']='mesh.obj'
    manifest={'schema_version':1,'package_type':'perception_scan','source':args.source,'pose_source':'rtabmap','units':'metres','frame':'map','axes':{'x':'forward','y':'left','z':'up'},'T_realmforge_map':[[0,-1,0,0],[0,0,1,0],[-1,0,0,0],[0,0,0,1]],'files':files,'mapping':'RTAB-Map export','limitations':['export coordinates must already be in the same z-up map frame','source label supplied by operator','not validated for robot navigation']}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(args.output/'manifest.json')


if __name__=='__main__': main()
