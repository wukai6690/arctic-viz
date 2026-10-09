"""Move complete polygon parts near the viewport; never alter canonical source geometry."""
import math

def near_longitude(longitude,center):
    return longitude+360*math.floor((center-longitude+180)/360)

def geometry_near_longitude(obj,center):
    kind=obj['type']
    if kind=='FeatureCollection':return {**obj,'features':[geometry_near_longitude(f,center) for f in obj['features']]}
    if kind=='Feature':return {**obj,'geometry':geometry_near_longitude(obj['geometry'],center)}
    if kind=='GeometryCollection':return {**obj,'geometries':[geometry_near_longitude(g,center) for g in obj['geometries']]}
    def polygon(rings):
        if not rings:return rings
        longitudes=[p[0] for p in rings[0]];anchor=(min(longitudes)+max(longitudes))/2
        shift=near_longitude(anchor,center)-anchor
        return [[[p[0]+shift,*p[1:]] for p in ring] for ring in rings]
    if kind=='Polygon':return {**obj,'coordinates':polygon(obj['coordinates'])}
    if kind=='MultiPolygon':return {**obj,'coordinates':[polygon(p) for p in obj['coordinates']]}
    if kind=='Point':return {**obj,'coordinates':[near_longitude(obj['coordinates'][0],center),*obj['coordinates'][1:]]}
    return obj
