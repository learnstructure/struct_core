from struct_core import load_json
from struct_core.project import Project
from fem2d import (from_schema, Results)

# Example of importing a JSON file directly into a struct_core Project object
project = load_json(Project, "examples/portal_frame_project.json")

structure = from_schema(project)

structure.solve()
results = Results(structure)
print(results.node_displacements())

# print(structure.elements[1].local_stiffness())
