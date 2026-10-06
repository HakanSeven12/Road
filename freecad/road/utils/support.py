import FreeCAD

def zero_reference(reference, points):
    #return [FreeCAD.Vector(*p).multiply(1000) for p in points]
    ref = FreeCAD.Vector(*reference)
    vectors = []
    for i in points:
        vec = FreeCAD.Vector(*i).sub(ref)
        vectors.append(vec.multiply(1000))
    
    return vectors