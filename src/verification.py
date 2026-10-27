"""B-Rep checks adapted from sw-agent/model_validation/cad.py."""
from solidworks.com_utils import com_prop, verify_rebuild


def measure(doc):
    rebuilt, issues = verify_rebuild(doc)
    bodies = list(doc.GetBodies2(0, False) or [])
    boxes = [list(com_prop(body, 'GetBodyBox')) for body in bodies]
    bounds = ([min(b[i] for b in boxes)*1000 for i in range(3)] +
              [max(b[i+3] for b in boxes)*1000 for i in range(3)]) if boxes else []
    mass = com_prop(doc, 'GetMassProperties')
    cylinders = []
    for body in bodies:
        for face in com_prop(body, 'GetFaces') or []:
            surface = com_prop(face, 'GetSurface')
            if com_prop(surface, 'IsCylinder'):
                params = list(com_prop(surface, 'CylinderParams'))
                i = max(range(3), key=lambda j: abs(params[j+3]))
                box = list(com_prop(face, 'GetBox'))
                cylinders.append({'center_mm':[v*1000 for v in params[:3]],
                    'axis':params[3:6], 'radius_mm':params[6]*1000,
                    'length_mm':abs(box[i+3]-box[i])*1000})
    return {'body_count':len(bodies), 'bounds_mm':bounds,
            'volume_mm3':mass[3]*1e9 if mass is not None else None,
            'cylinders':cylinders, 'rebuild_ok':rebuilt, 'rebuild_issues':issues}
