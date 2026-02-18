import FreeCAD

def zero_referance(referance, points):
    #return [FreeCAD.Vector(*p).multiply(1000) for p in points]
    ref = FreeCAD.Vector(*referance)
    vectors = []
    for i in points:
        vec = FreeCAD.Vector(*i).sub(ref)
        vectors.append(vec.multiply(1000))
    
    return vectors