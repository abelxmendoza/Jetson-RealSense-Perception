"""Consumer adapters: conservative rover grid and native RealmForge world JSON."""
from datetime import datetime, timezone
import heapq
import json
import math
from pathlib import Path
import numpy as np


class RoverMap:
    def __init__(self, grid, resolution, origin):
        raw=np.asarray(grid)
        if not np.isin(raw,[-1,0,100]).all():
            raise ValueError("invalid occupancy values before conversion")
        self.grid=raw.astype(np.int8)
        self.resolution=float(resolution)
        self.origin=np.asarray(origin,dtype=float)
        if self.grid.ndim!=2 or not np.isin(self.grid,[-1,0,100]).all():
            raise ValueError('expected 2D grid with unknown=-1, free=0, occupied=100')
        if not math.isfinite(self.resolution) or self.resolution<=0 or self.origin.shape!=(2,) or not np.isfinite(self.origin).all():
            raise ValueError('invalid map geometry')

    @classmethod
    def load(cls,path):
        d=json.loads(Path(path).read_text())
        if d.get('format')!='omega-occupancy' or d.get('version')!=1 or d.get('frame')!='map' or d.get('units')!='metres':
            raise ValueError('unsupported Omega occupancy format')
        if d.get('row_order')!='increasing_y': raise ValueError('unsupported row order')
        return cls(d['cells'],d['resolution_m'],d['origin_xy'])

    def cell(self,point):
        if len(point)!=2 or not np.isfinite(point).all(): raise ValueError('point must be finite x,y')
        x,y=np.floor((np.asarray(point)-self.origin)/self.resolution).astype(int)
        return int(x),int(y)

    def blocked(self,radius):
        if not math.isfinite(radius) or radius<0: raise ValueError('radius must be finite and nonnegative')
        blocked=self.grid!=0  # unknown is blocked
        result=blocked.copy()
        n=math.ceil(radius/self.resolution)
        h,w=blocked.shape
        # Cell-centre distance plus half-cell diagonals conservatively covers footprint.
        for dy in range(-n-1,n+2):
            for dx in range(-n-1,n+2):
                if math.hypot(max(0,abs(dx)-.5),max(0,abs(dy)-.5))*self.resolution>radius: continue
                ys,ye=max(0,dy),min(h,h+dy);xs,xe=max(0,dx),min(w,w+dx)
                if ys<ye and xs<xe: result[ys:ye,xs:xe] |= blocked[ys-dy:ye-dy,xs-dx:xe-dx]
        # Treat outside-map space as occupied.
        if n:
            result[:n,:]=result[-n:,:]=True;result[:,:n]=result[:,-n:]=True
        return result

    def plan(self,start,goal,radius=.2):
        blocked=self.blocked(radius);h,w=blocked.shape
        start,goal=self.cell(start),self.cell(goal)
        def free(c): return 0<=c[0]<w and 0<=c[1]<h and not blocked[c[1],c[0]]
        if not free(start) or not free(goal): raise ValueError('start or goal is blocked, unknown, or outside map')
        queue=[(0,start)];cost={start:0};parents={}
        while queue:
            _,cur=heapq.heappop(queue)
            if cur==goal:
                route=[cur]
                while cur!=start: cur=parents[cur];route.append(cur)
                return [(self.origin+(np.array(c)+.5)*self.resolution).tolist() for c in reversed(route)]
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nxt=(cur[0]+dx,cur[1]+dy);g=cost[cur]+1
                if free(nxt) and g<cost.get(nxt,float('inf')):
                    cost[nxt]=g;parents[nxt]=cur
                    heapq.heappush(queue,(g+abs(nxt[0]-goal[0])+abs(nxt[1]-goal[1]),nxt))
        raise ValueError('no route through observed free space')


def realmforge_world(rover_map,name='Scanned room'):
    objects=[]
    # Row runs compress blocked cells without declaring unseen areas traversable.
    for y,row in enumerate(rover_map.grid):
        x=0
        while x<len(row):
            if row[x]==0: x+=1;continue
            end=x+1
            while end<len(row) and row[end]==row[x]: end+=1
            map_x=rover_map.origin[0]+(x+end)*.5*rover_map.resolution
            map_y=rover_map.origin[1]+(y+.5)*rover_map.resolution
            objects.append({'id':f'scan-{y}-{x}','kind':'wall','position':[-float(map_y),0.,-float(map_x)],'size':[rover_map.resolution,1.5,(end-x)*rover_map.resolution],'rotationY':0.,'solid':True,'color':'#555555' if row[x]==-1 else '#b87832'})
            x=end
    if len(objects)>2000: raise ValueError('RealmForge limit exceeded; use a coarser scan grid')
    return {'format':'realmforge-world','version':1,'name':name[:80],'savedAt':datetime.now(timezone.utc).isoformat(),'environmentId':'empty-event-venue','objects':objects,'robotEnabled':False,'robotStart':[0,0],'goal':None}
