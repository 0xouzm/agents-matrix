"""Draw.io Diagram Agent — skill definitions, system prompt, agent card."""

from __future__ import annotations

from a2a.types import AgentCard, AgentSkill, AgentCapabilities, AgentInterface

from agents_core.settings import Settings

SYSTEM_PROMPT = (
    "You are a diagram creation agent powered by draw.io (cli-anything-drawio). "
    "You can create, edit, and export diagrams programmatically.\n\n"
    "WORKFLOW — always follow this order:\n"
    "1. Create a new project (create_project) or open an existing one (open_project)\n"
    "2. Add shapes (add_shape) — 15 types: rectangle, rounded, ellipse, diamond, "
    "triangle, hexagon, cylinder, cloud, parallelogram, process, document, callout, "
    "note, actor, text\n"
    "3. Connect shapes (add_connector) — 4 edge styles: straight, orthogonal, curved, "
    "entity-relation\n"
    "4. Export the diagram (export_diagram) — formats: png, pdf, svg, vsdx, xml\n\n"
    "IMPORTANT:\n"
    "- You MUST create or open a project before adding shapes or connectors.\n"
    "- Shape IDs are returned by add_shape — use them for connectors and references.\n"
    "- The session is stateful: undo/redo is supported via get_session_status.\n"
    "- Multi-page diagrams are supported: pass a page index to shape/connector tools.\n"
    "- When the user describes a diagram, plan the layout (x, y coordinates) to avoid "
    "overlapping shapes. Use a grid spacing of ~150px between shapes.\n"
    "- Always save or export when the user's request is complete.\n"
    "- Provide a summary of what was created (shape count, connections, export path)."
)

SKILLS: list[AgentSkill] = [
    AgentSkill(
        id="diagram_create",
        name="Create Diagram",
        description="Create a new draw.io diagram project with optional page size presets (letter, A4, 16:9, etc.).",
        tags=["diagram", "create", "project", "drawio"],
        examples=[
            "Create a new diagram",
            "Start a new A4-sized diagram",
        ],
    ),
    AgentSkill(
        id="shape_manage",
        name="Manage Shapes",
        description="Add, remove, and list shapes in a diagram. Supports 15 shape types including rectangles, ellipses, diamonds, and more.",
        tags=["shape", "add", "remove", "list", "drawio"],
        examples=[
            "Add a rectangle labeled 'Server' at position (100, 200)",
            "List all shapes on the current page",
        ],
    ),
    AgentSkill(
        id="connector_manage",
        name="Manage Connectors",
        description="Add and manage connectors between shapes. Supports straight, orthogonal, curved, and entity-relation edge styles.",
        tags=["connector", "edge", "connect", "drawio"],
        examples=[
            "Connect shape A to shape B with an orthogonal line",
            "Add a labeled arrow from the database to the server",
        ],
    ),
    AgentSkill(
        id="diagram_export",
        name="Export Diagram",
        description="Export diagrams to PNG, PDF, SVG, VSDX, or XML formats with optional scaling and cropping.",
        tags=["export", "render", "png", "pdf", "svg", "drawio"],
        examples=[
            "Export the diagram as PNG",
            "Save the diagram as architecture.pdf",
        ],
    ),
]


def build_agent_card(settings: Settings) -> AgentCard:
    return AgentCard(
        name="Draw.io Diagram Agent",
        description=(
            "Paid AI agent for diagram creation and editing — create projects, "
            "add shapes, connect them, and export to PNG/PDF/SVG. "
            "Powered by draw.io. Accepts USDC payment via x402 protocol."
        ),
        supported_interfaces=[AgentInterface(url=settings.base_url + "/")],
        version="0.1.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        skills=SKILLS,
    )
