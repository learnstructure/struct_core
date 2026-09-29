from struct_core import load_json
from struct_core.project import Project
from fem2d import (model_from_core, Results)

# Example of importing a JSON file directly into a struct_core Project object
project = load_json(Project, "examples/portal_frame_project.json")

structure = model_from_core(project)

structure.solve()
results = Results(structure)
print(results.node_displacements())

# print(structure.elements[1].local_stiffness())
