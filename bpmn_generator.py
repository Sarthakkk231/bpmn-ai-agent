
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


# ==================================================
# 1. BPMN 2.0 NAMESPACES
# ==================================================

BPMN_NAMESPACE = (
    "http://www.omg.org/spec/BPMN/20100524/MODEL"
)

BPMNDI_NAMESPACE = (
    "http://www.omg.org/spec/BPMN/20100524/DI"
)

DC_NAMESPACE = (
    "http://www.omg.org/spec/DD/20100524/DC"
)

DI_NAMESPACE = (
    "http://www.omg.org/spec/DD/20100524/DI"
)

XSI_NAMESPACE = (
    "http://www.w3.org/2001/XMLSchema-instance"
)


ET.register_namespace("bpmn", BPMN_NAMESPACE)
ET.register_namespace("bpmndi", BPMNDI_NAMESPACE)
ET.register_namespace("dc", DC_NAMESPACE)
ET.register_namespace("di", DI_NAMESPACE)
ET.register_namespace("xsi", XSI_NAMESPACE)


# ==================================================
# 2. HELPER FUNCTION FOR XML TAGS
# ==================================================

def qname(namespace, tag):

    return "{" + namespace + "}" + tag


# ==================================================
# 3. BPMN ELEMENT TYPE MAPPING
# ==================================================

BPMN_ELEMENT_MAPPING = {

    "start_event": "startEvent",

    "end_event": "endEvent",

    "task": "task",

    "user_task": "userTask",

    "service_task": "serviceTask",

    "exclusive_gateway": "exclusiveGateway",

    "parallel_gateway": "parallelGateway"

}


# ==================================================
# 4. CREATE BPMN DEFINITIONS
# ==================================================

def create_definitions(process_name):

    definitions = ET.Element(
        qname(BPMN_NAMESPACE, "definitions"),
        {
            "id": "Definitions_1",
            "targetNamespace": "http://example.com/bpmn"
        }
    )

    return definitions


# ==================================================
# 5. CREATE BPMN PROCESS
# ==================================================

def create_process(definitions, process_name):

    process = ET.SubElement(
        definitions,
        qname(BPMN_NAMESPACE, "process"),
        {
            "id": "Process_1",
            "name": str(process_name),
            "isExecutable": "false"
        }
    )

    return process


# ==================================================
# 6. GENERATE BPMN FLOW ELEMENTS
# ==================================================

def create_bpmn_elements(process, elements):

    for element in elements:

        element_id = element["id"]

        element_name = element.get(
            "name",
            element_id
        )

        element_type = element["type"]

        bpmn_tag = BPMN_ELEMENT_MAPPING.get(
            element_type
        )

        if not bpmn_tag:

            raise ValueError(
                "Unsupported BPMN element type: "
                + str(element_type)
            )

        ET.SubElement(
            process,
            qname(BPMN_NAMESPACE, bpmn_tag),
            {
                "id": element_id,
                "name": str(element_name)
            }
        )


# ==================================================
# 7. GENERATE BPMN SEQUENCE FLOWS
# ==================================================

def create_sequence_flows(process, sequence_flows):

    for flow in sequence_flows:

        attributes = {

            "id": flow["id"],

            "sourceRef": flow["from"],

            "targetRef": flow["to"]

        }

        sequence_flow = ET.SubElement(
            process,
            qname(BPMN_NAMESPACE, "sequenceFlow"),
            attributes
        )

        condition = flow.get("condition")

        if condition:

            condition_expression = ET.SubElement(
                sequence_flow,
                qname(BPMN_NAMESPACE, "conditionExpression"),
                {
                    qname(XSI_NAMESPACE, "type"):
                        "bpmn:tFormalExpression"
                }
            )

            condition_expression.text = str(condition)


# ==================================================
# 8. BUILD GRAPH INFORMATION
# ==================================================

def build_graph(elements, sequence_flows):

    element_ids = {
        element["id"] for element in elements
    }

    outgoing = {
        element_id: [] for element_id in element_ids
    }

    incoming = {
        element_id: [] for element_id in element_ids
    }

    for flow in sequence_flows:

        source = flow["from"]

        target = flow["to"]

        if source not in element_ids:
            raise ValueError(
                "Sequence flow references unknown source: "
                + str(source)
            )

        if target not in element_ids:
            raise ValueError(
                "Sequence flow references unknown target: "
                + str(target)
            )

        outgoing[source].append(target)

        incoming[target].append(source)

    return outgoing, incoming


# ==================================================
# 9. CALCULATE HORIZONTAL LEVELS
# ==================================================

def calculate_element_levels(elements, outgoing, incoming):

    element_ids = [
        element["id"] for element in elements
    ]

    levels = {}

    pending = {
        element_id: len(incoming[element_id])
        for element_id in element_ids
    }

    queue = [
        element_id
        for element_id in element_ids
        if pending[element_id] == 0
    ]

    for element_id in queue:
        levels[element_id] = 0

    processed = 0

    while queue:

        current = queue.pop(0)

        processed += 1

        for target in outgoing[current]:

            levels[target] = max(
                levels.get(target, 0),
                levels[current] + 1
            )

            pending[target] -= 1

            if pending[target] == 0:
                queue.append(target)

    if processed != len(element_ids):

        raise ValueError(
            "The layout generator currently supports "
            "acyclic workflows only. A cycle was detected."
        )

    return levels


# ==================================================
# 10. CALCULATE VERTICAL LANES
# ==================================================

def calculate_element_lanes(
    elements,
    outgoing,
    incoming
):

    element_ids = [
        element["id"] for element in elements
    ]

    element_types = {
        element["id"]: element["type"]
        for element in elements
    }

    # ----------------------------------------------
    # Find parallel gateways that split branches
    # ----------------------------------------------

    parallel_splits = []

    for element_id in element_ids:

        if (
            element_types[element_id] == "parallel_gateway"
            and len(outgoing[element_id]) > 1
        ):

            parallel_splits.append(element_id)

    max_branches = max(
        [
            len(outgoing[split])
            for split in parallel_splits
        ],
        default=1
    )

    start_y = 150

    vertical_spacing = 140

    center_y = (
        start_y
        + ((max_branches - 1) * vertical_spacing / 2)
    )

    # Initially place all elements on the center line.

    lanes = {
        element_id: center_y
        for element_id in element_ids
    }

    join_lanes = {}

    # ----------------------------------------------
    # Trace each parallel branch
    # ----------------------------------------------

    for split_id in parallel_splits:

        branches = outgoing[split_id]

        for branch_index, branch_start in enumerate(branches):

            branch_y = (
                start_y
                + branch_index * vertical_spacing
            )

            queue = [branch_start]

            visited = set()

            while queue:

                current = queue.pop(0)

                if current in visited:
                    continue

                visited.add(current)

                # Stop when reaching a parallel join.

                is_parallel_join = (
                    element_types[current] == "parallel_gateway"
                    and len(incoming[current]) > 1
                )

                if is_parallel_join:

                    if current not in join_lanes:
                        join_lanes[current] = []

                    join_lanes[current].append(branch_y)

                    continue

                lanes[current] = branch_y

                for target in outgoing[current]:
                    queue.append(target)

    # ----------------------------------------------
    # Center joining gateways between their branches
    # ----------------------------------------------

    for join_id, branch_positions in join_lanes.items():

        lanes[join_id] = (
            sum(branch_positions) / len(branch_positions)
        )

    # ----------------------------------------------
    # Propagate the center position after a join
    # ----------------------------------------------

    for join_id in join_lanes:

        queue = list(outgoing[join_id])

        visited = set()

        while queue:

            current = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            # Do not interfere with another split.

            is_parallel_split = (
                element_types[current] == "parallel_gateway"
                and len(outgoing[current]) > 1
            )

            if is_parallel_split:
                continue

            lanes[current] = lanes[join_id]

            for target in outgoing[current]:
                queue.append(target)

    return lanes


# ==================================================
# 11. CALCULATE ELEMENT POSITIONS
# ==================================================

def calculate_element_positions(elements, sequence_flows):

    outgoing, incoming = build_graph(
        elements,
        sequence_flows
    )

    levels = calculate_element_levels(
        elements,
        outgoing,
        incoming
    )

    lanes = calculate_element_lanes(
        elements,
        outgoing,
        incoming
    )

    start_x = 100

    horizontal_spacing = 180

    element_positions = {}

    for element in elements:

        element_id = element["id"]

        element_type = element["type"]

        x = (
            start_x
            + levels[element_id] * horizontal_spacing
        )

        y = lanes[element_id]

        if element_type in [
            "start_event",
            "end_event"
        ]:

            width = 36
            height = 36

        elif element_type in [
            "exclusive_gateway",
            "parallel_gateway"
        ]:

            width = 50
            height = 50

        else:

            width = 100
            height = 80

        element_positions[element_id] = {

            "x": x,

            "y": y,

            "width": width,

            "height": height

        }

    return element_positions


# ==================================================
# 12. CREATE BPMN SHAPES
# ==================================================

def create_bpmn_shapes(plane, elements, positions):

    for element in elements:

        element_id = element["id"]

        position = positions[element_id]

        shape = ET.SubElement(
            plane,
            qname(BPMNDI_NAMESPACE, "BPMNShape"),
            {
                "id": element_id + "_di",
                "bpmnElement": element_id
            }
        )

        ET.SubElement(
            shape,
            qname(DC_NAMESPACE, "Bounds"),
            {
                "x": str(position["x"]),
                "y": str(position["y"]),
                "width": str(position["width"]),
                "height": str(position["height"])
            }
        )


# ==================================================
# 13. CREATE EDGE WAYPOINTS
# ==================================================

def create_edge_waypoints(edge, source, target):

    source_center_x = (
        source["x"] + source["width"] / 2
    )

    source_center_y = (
        source["y"] + source["height"] / 2
    )

    target_center_x = (
        target["x"] + target["width"] / 2
    )

    target_center_y = (
        target["y"] + target["height"] / 2
    )

    # ----------------------------------------------
    # Normal left-to-right connection
    # ----------------------------------------------

    if target_center_x > source_center_x:

        start_x = source["x"] + source["width"]

        start_y = source_center_y

        end_x = target["x"]

        end_y = target_center_y

        middle_x = (start_x + end_x) / 2

        waypoints = [

            (start_x, start_y),

            (middle_x, start_y),

            (middle_x, end_y),

            (end_x, end_y)

        ]

    # ----------------------------------------------
    # Vertical connection
    # ----------------------------------------------

    elif target_center_x == source_center_x:

        if target_center_y >= source_center_y:

            start_y = source["y"] + source["height"]

            end_y = target["y"]

        else:

            start_y = source["y"]

            end_y = target["y"] + target["height"]

        waypoints = [

            (source_center_x, start_y),

            (target_center_x, end_y)

        ]

    # ----------------------------------------------
    # Backward connection
    # ----------------------------------------------

    else:

        start_x = source["x"]

        start_y = source_center_y

        end_x = target["x"] + target["width"]

        end_y = target_center_y

        middle_x = (start_x + end_x) / 2

        waypoints = [

            (start_x, start_y),

            (middle_x, start_y),

            (middle_x, end_y),

            (end_x, end_y)

        ]

    for x, y in waypoints:

        ET.SubElement(
            edge,
            qname(DI_NAMESPACE, "waypoint"),
            {
                "x": str(x),
                "y": str(y)
            }
        )


# ==================================================
# 14. CREATE BPMN EDGES
# ==================================================

def create_bpmn_edges(plane, sequence_flows, positions):

    for flow in sequence_flows:

        source = positions[flow["from"]]

        target = positions[flow["to"]]

        edge = ET.SubElement(
            plane,
            qname(BPMNDI_NAMESPACE, "BPMNEdge"),
            {
                "id": flow["id"] + "_di",
                "bpmnElement": flow["id"]
            }
        )

        create_edge_waypoints(
            edge,
            source,
            target
        )


# ==================================================
# 15. CREATE BPMN DIAGRAM
# ==================================================

def create_bpmn_diagram(definitions, data):

    diagram = ET.SubElement(
        definitions,
        qname(BPMNDI_NAMESPACE, "BPMNDiagram"),
        {
            "id": "BPMNDiagram_1"
        }
    )

    plane = ET.SubElement(
        diagram,
        qname(BPMNDI_NAMESPACE, "BPMNPlane"),
        {
            "id": "BPMNPlane_1",
            "bpmnElement": "Process_1"
        }
    )

    elements = data["elements"]

    sequence_flows = data["sequence_flows"]

    positions = calculate_element_positions(
        elements,
        sequence_flows
    )

    create_bpmn_shapes(
        plane,
        elements,
        positions
    )

    create_bpmn_edges(
        plane,
        sequence_flows,
        positions
    )


# ==================================================
# 16. CONVERT JSON INTO BPMN 2.0 XML
# ==================================================

def generate_bpmn_xml(data):

    if not isinstance(data, dict):

        raise ValueError(
            "BPMN input must be a dictionary."
        )

    process_name = data.get(
        "process_name",
        "Generated Process"
    )

    elements = data.get("elements")

    sequence_flows = data.get("sequence_flows")

    if not isinstance(elements, list) or not elements:

        raise ValueError(
            "BPMN elements must be a non-empty list."
        )

    if not isinstance(sequence_flows, list):

        raise ValueError(
            "BPMN sequence flows must be a list."
        )

    # ----------------------------------------------
    # Create BPMN definitions
    # ----------------------------------------------

    definitions = create_definitions(
        process_name
    )

    # ----------------------------------------------
    # Create BPMN process
    # ----------------------------------------------

    create_process(
        definitions,
        process_name
    )

    # ----------------------------------------------
    # Generate BPMN elements
    # ----------------------------------------------

    process = definitions.find(
        qname(BPMN_NAMESPACE, "process")
    )

    create_bpmn_elements(
        process,
        elements
    )

    # ----------------------------------------------
    # Generate sequence flows
    # ----------------------------------------------

    create_sequence_flows(
        process,
        sequence_flows
    )

    # ----------------------------------------------
    # Generate diagram information
    # ----------------------------------------------

    create_bpmn_diagram(
        definitions,
        data
    )

    # ----------------------------------------------
    # Convert XML tree to string
    # ----------------------------------------------

    xml_bytes = ET.tostring(
        definitions,
        encoding="utf-8"
    )

    parsed_xml = minidom.parseString(
        xml_bytes
    )

    formatted_xml = parsed_xml.toprettyxml(
        indent="    ",
        encoding="UTF-8"
    )

    return formatted_xml.decode("utf-8")


# ==================================================
# 17. SAVE BPMN XML FILE
# ==================================================

def save_bpmn_xml(xml_content, filename):

    output_directory = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "generated_bpmn"
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    file_path = os.path.join(
        output_directory,
        filename
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(xml_content)

    return file_path
