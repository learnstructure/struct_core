"""
Local axes and shape checks of shell elements (struct_core.geometry).

A slab panel meets a wall along y = 0. The local axes follow SAP2000 (CSI Analysis Reference Manual §10.6): the slab
has axis 3 up and axes 1, 2 along global X, Y; the wall has axis 2 up. The checks of CSI §10.2.1 report a skewed
panel, and the normal check finds a slab element numbered the wrong way round.
"""

from struct_core import ConcreteMaterial, Node, ShellElement, ShellSection, StructuralModel
from struct_core.geometry import check_model_shells, model_shell_axes

points = {1: (0, 0, 3), 2: (4, 0, 3), 3: (4, 3, 3), 4: (0, 3, 3), 5: (0, 0, 0), 6: (4, 0, 0),
          7: (8, 0, 3), 8: (11.5, 3, 3)}
model = StructuralModel(
    units="kN, m",
    nodes=[Node(id=k, x=x, y=y, z=z) for k, (x, y, z) in points.items()],
    materials=[ConcreteMaterial(id="C30", E=25e6, fc=30e3, unit_weight=24.0)],
    shell_sections=[ShellSection(id="SLAB", material_id="C30", thickness=0.2),
                    ShellSection(id="WALL", material_id="C30", thickness=0.25)],
    shell_elements=[
        ShellElement(id="S1", node_ids=[1, 2, 3, 4], section_id="SLAB"),
        ShellElement(id="S2", node_ids=[2, 3, 8, 7], section_id="SLAB"),  # skewed, and numbered clockwise
        ShellElement(id="W1", node_ids=[5, 6, 2, 1], section_id="WALL"),
    ],
)

for eid, axes in model_shell_axes(model).items():
    print(eid, "axis 1", axes[0].round(3), "axis 2", axes[1].round(3), "axis 3", axes[2].round(3))

for issue in check_model_shells(model):
    print(f"[{issue.severity}] {issue.message}")
