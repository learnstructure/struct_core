"""
Example demonstrating how to build a portal frame using struct_core JSON / Pydantic models,
convert it using fem2d.model_from_core(), and solve for static displacements and internal forces.
"""

from struct_core import (
    BeamElement,
    DistributedLoad,
    ElasticMaterial,
    LinearStaticAnalysis,
    LoadCase,
    Node,
    PointLoad,
    Project,
    RectangularSection,
    StructuralModel,
    Support,
    from_json,
    save_json,
)

from fem2d import model_from_core


def main():
    print("=== Step 1: Building Structural Model via struct_schema ===")

    # Portal Frame Geometry: 6m span x 4m height
    model = StructuralModel(
        nodes=[
            Node(id=1, x=0.0, y=0.0),  # Base left
            Node(id=2, x=0.0, y=4.0),  # Top left joint
            Node(id=3, x=6.0, y=4.0),  # Top right joint
            Node(id=4, x=6.0, y=0.0),  # Base right
        ],
        materials=[
            ElasticMaterial(id="StructuralSteel", E=200e9, rho=7850.0),
        ],
        sections=[
            RectangularSection(id="ColSec", b=0.30, h=0.30),
            RectangularSection(id="BeamSec", b=0.25, h=0.45),
        ],
        elements=[
            BeamElement(id=1, start_node=1, end_node=2, material_id="StructuralSteel", section_id="ColSec"),
            BeamElement(id=2, start_node=2, end_node=3, material_id="StructuralSteel", section_id="BeamSec"),
            BeamElement(id=3, start_node=3, end_node=4, material_id="StructuralSteel", section_id="ColSec"),
        ],
        supports=[
            Support.fixed(node_id=1, name="Left Support"),
            Support.fixed(node_id=4, name="Right Support"),
        ],
        load_cases=[
            LoadCase(
                id="GravityAndWind",
                name="Dead Load + Lateral Wind",
                point_loads=[
                    PointLoad(node_id=2, fx=20e3),  # 20 kN horizontal wind load at top joint
                ],
                element_loads=[
                    DistributedLoad(element_id=2, wy=-15e3),  # 15 kN/m downward load on beam
                ],
            )
        ],
        analysis_cases=[
            LinearStaticAnalysis(id="LinearSolve", load_case_id="GravityAndWind"),
        ],
    )

    project = Project()
    project.metadata.title = "2D Portal Frame Example"
    project.metadata.project_name = "Industrial Warehouse"
    project.metadata.author = "Structural Engineer AI"
    project.model = model

    # Save the project directly to a JSON file
    output_path = "examples/portal_frame_project.json"
    save_json(project, output_path, indent=2)
    print(f"Project saved to {output_path}")

    # Deserialize from JSON
    reloaded_project = from_json(Project, open(output_path, "r", encoding="utf-8").read())

    print("\n=== Step 2: Converting Schema to fem2d.Structure via Adapter ===")
    structure = model_from_core(reloaded_project)
    print(f"Created Structure with {len(structure.nodes)} nodes and {len(structure.elements)} elements.")

    # print("\n=== Step 3: Solving Linear Static Analysis ===")
    # structure.solve()

    # print("\n=== Step 4: Displacements Output ===")
    # for nid, node in sorted(structure.nodes.items()):
    #     dofs = node.dofs
    #     ux = structure.disp[dofs[0]]
    #     uy = structure.disp[dofs[1]]
    #     rz = structure.disp[dofs[2]]
    #     print(
    #         f"Node {nid:2d} (x={node.x:3.1f}m, y={node.y:3.1f}m): "
    #         f"Ux = {ux * 1e3:7.3f} mm, Uy = {uy * 1e3:7.3f} mm, Rz = {rz * 1e3:7.3f} rad/1000"
    #     )

    # print("\nSuccess! Adapter integrated seamlessly with fem2d.")


if __name__ == "__main__":
    main()
