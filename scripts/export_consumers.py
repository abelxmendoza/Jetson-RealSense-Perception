#!/usr/bin/env python3
"""Export native RealmForge world JSON and Omega occupancy from a scan package."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jetson_realsense_perception.scan_consumers import RoverMap, realmforge_world
from jetson_realsense_perception.scan_contract import validate_scan, read_pgm


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scan',type=Path)
    parser.add_argument('output',type=Path,help='new directory')
    parser.add_argument('--start',nargs=2,type=float)
    parser.add_argument('--goal',nargs=2,type=float)
    parser.add_argument('--radius',type=float,default=.2)
    args=parser.parse_args()
    if bool(args.start) != bool(args.goal): parser.error('supply both --start and --goal')
    manifest=validate_scan(args.scan)
    if manifest.get('schema_version')!=1 or manifest.get('package_type')!='perception_scan' or manifest.get('units')!='metres' or manifest.get('frame')!='map': parser.error('unsupported scan package')
    # Strictly consume this producer format; arbitrary YAML/PGM parsers are not needed.
    if 'occupancy' not in manifest: parser.error('requires build_scan package with occupancy metadata; RTAB exports need a dedicated YAML importer')
    pixels=read_pgm(args.scan/'map.pgm')[::-1]
    grid=np.where(pixels==0,100,np.where(pixels==254,0,-1)).astype(np.int8)
    info=manifest['occupancy'];rover=RoverMap(grid,info['resolution_m'],info['origin_xy'])
    world=realmforge_world(rover,name=f'{manifest["source"]} scanned room')
    world['savedAt']=datetime.now(timezone.utc).isoformat()
    route=rover.plan(args.start,args.goal,args.radius) if args.start else None
    omega={'format':'omega-occupancy','version':1,'source':manifest['source'],'units':'metres','frame':'map','row_order':'increasing_y','resolution_m':rover.resolution,'origin_xy':rover.origin.tolist(),'cells':grid.tolist(),'route_xy':route,'footprint_radius_m':args.radius,'localization':'not provided; map-to-Omega transform required'}
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'realmforge-world.json').write_text(json.dumps(world,indent=2))
    (args.output/'omega-map.json').write_text(json.dumps(omega))
    print(json.dumps({'output':str(args.output),'realmforge_blockers':len(world['objects']),'route_points':len(route) if route else 0},indent=2))

if __name__=='__main__': main()
