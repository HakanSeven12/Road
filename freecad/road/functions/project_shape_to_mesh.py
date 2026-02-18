import FreeCAD
import MeshPart

def project_shape_to_mesh(shape_obj, mesh_obj):
    """
    Project shape object onto mesh object.
    """
    flat_points = []

    # Get intersection points between shape and mesh
    for edge in shape_obj.Shape.Edges:
        params = MeshPart.findSectionParameters(
            edge, mesh_obj.Mesh, FreeCAD.Vector(0, 0, 1))
        params.insert(0, edge.FirstParameter+1)
        params.append(edge.LastParameter-1)

        values = [edge.valueAt(glp) for glp in params]
        flat_points.extend(values)

    # Project points onto mesh
    projected_points = MeshPart.projectPointsOnMesh(
        flat_points, mesh_obj.Mesh, FreeCAD.Vector(0, 0, 1))
    
    return projected_points
            