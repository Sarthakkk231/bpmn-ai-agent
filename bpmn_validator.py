import xml.etree.ElementTree as ET
from pathlib import Path

from lxml import etree


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


# ==================================================
# 2. SCHEMA CONFIGURATION
# ==================================================

SCHEMA_DIRECTORY = (
    Path(__file__).resolve().parent / "bpmn_schemas"
)

MAIN_SCHEMA_FILE = (
    SCHEMA_DIRECTORY / "BPMN20.xsd"
)


# ==================================================
# 3. HELPER FUNCTIONS
# ==================================================

def qname(namespace, tag):
    return "{" + namespace + "}" + tag


def get_element_id(element):
    return element.get("id")


# ==================================================
# 4. BPMN ELEMENT DEFINITIONS
# ==================================================

SUPPORTED_FLOW_ELEMENTS = {
    "startEvent",
    "endEvent",
    "task",
    "userTask",
    "serviceTask",
    "exclusiveGateway",
    "parallelGateway"
}


# ==================================================
# 5. VALIDATE XML SYNTAX
# ==================================================

def validate_xml_syntax(xml_content):

    try:
        root = ET.fromstring(xml_content)

        return root, []

    except ET.ParseError as error:

        return None, [
            "Invalid XML syntax: " + str(error)
        ]


# ==================================================
# 6. OFFICIAL BPMN 2.0 XSD VALIDATION
# ==================================================

def validate_bpmn_xsd(xml_content):
    """
    Validate XML against the official BPMN 2.0 XSD schema.

    The main BPMN20.xsd file imports/includes other schemas.
    All schema files must be present in bpmn_schemas.
    """

    if not MAIN_SCHEMA_FILE.exists():

        return [
            "Official BPMN XSD schema not found: "
            + str(MAIN_SCHEMA_FILE)
        ]

    required_files = [
        "BPMN20.xsd",
        "BPMNDI.xsd",
        "DC.xsd",
        "DI.xsd",
        "Semantic.xsd"
    ]

    missing_files = []

    for filename in required_files:

        schema_file = SCHEMA_DIRECTORY / filename

        if not schema_file.exists():

            missing_files.append(filename)

    if missing_files:

        return [
            "Missing BPMN schema files: "
            + ", ".join(missing_files)
        ]

    try:

        # ------------------------------------------
        # Configure secure XML parser
        # ------------------------------------------

        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            remove_comments=False
        )

        # ------------------------------------------
        # Load the official BPMN XSD
        # ------------------------------------------

        schema_document = etree.parse(
            str(MAIN_SCHEMA_FILE),
            parser
        )

        schema = etree.XMLSchema(
            schema_document
        )

        # ------------------------------------------
        # Parse generated BPMN XML
        # ------------------------------------------

        if isinstance(xml_content, str):

            xml_content = xml_content.encode("utf-8")

        xml_document = etree.fromstring(
            xml_content,
            parser
        )

        # ------------------------------------------
        # Validate XML against XSD
        # ------------------------------------------

        schema.assertValid(xml_document)

        return []

    except etree.DocumentInvalid as error:

        errors = []

        for entry in error.error_log:

            errors.append(
                "BPMN XSD validation error: "
                + str(entry.message)
                + " (Line "
                + str(entry.line)
                + ")"
            )

        if not errors:

            errors.append(
                "Generated XML does not conform "
                "to the BPMN 2.0 XSD schema."
            )

        return errors

    except (etree.XMLSchemaParseError, etree.XMLSyntaxError,
            OSError, ValueError) as error:

        return [
            "BPMN XSD validation could not be completed: "
            + str(error)
        ]


# ==================================================
# 7. VALIDATE BPMN DEFINITIONS
# ==================================================

def validate_definitions(root):

    errors = []

    expected_tag = qname(
        BPMN_NAMESPACE,
        "definitions"
    )

    if root.tag != expected_tag:

        errors.append(
            "Root element must be BPMN definitions."
        )

    if not root.get("id"):

        errors.append(
            "BPMN definitions must have an ID."
        )

    if not root.get("targetNamespace"):

        errors.append(
            "BPMN definitions must have a targetNamespace."
        )

    return errors


# ==================================================
# 8. VALIDATE BPMN PROCESS
# ==================================================

def validate_process(root):

    errors = []

    processes = root.findall(
        qname(BPMN_NAMESPACE, "process")
    )

    if len(processes) != 1:

        errors.append(
            "The document must contain exactly one BPMN process."
        )

        return None, errors

    process = processes[0]

    if not process.get("id"):

        errors.append(
            "BPMN process must have an ID."
        )

    if process.get("isExecutable") not in [
        "true",
        "false"
    ]:

        errors.append(
            "BPMN process must define isExecutable as true or false."
        )

    return process, errors


# ==================================================
# 9. VALIDATE ELEMENT IDS
# ==================================================

def validate_element_ids(process):

    errors = []

    ids = {}

    for element in process.iter():

        element_id = get_element_id(element)

        if not element_id:
            continue

        if element_id in ids:

            errors.append(
                "Duplicate BPMN ID found: "
                + element_id
            )

        else:

            ids[element_id] = element

    return ids, errors


# ==================================================
# 10. VALIDATE FLOW ELEMENT TYPES
# ==================================================

def validate_flow_elements(process):

    errors = []

    flow_elements = []

    for child in list(process):

        tag = child.tag.split("}")[-1]

        if tag in SUPPORTED_FLOW_ELEMENTS:

            flow_elements.append(child)

            if not child.get("id"):

                errors.append(
                    tag + " must have an ID."
                )

            if not child.get("name"):

                errors.append(
                    tag + " must have a name."
                )

    if not flow_elements:

        errors.append(
            "BPMN process must contain flow elements."
        )

    return flow_elements, errors


# ==================================================
# 11. VALIDATE SEQUENCE FLOWS
# ==================================================

def validate_sequence_flows(process, ids):

    errors = []

    sequence_flows = process.findall(
        qname(BPMN_NAMESPACE, "sequenceFlow")
    )

    if not sequence_flows:

        errors.append(
            "BPMN process must contain sequence flows."
        )

    flow_pairs = set()

    for flow in sequence_flows:

        flow_id = flow.get("id")

        source = flow.get("sourceRef")

        target = flow.get("targetRef")

        if not flow_id:

            errors.append(
                "Sequence flow must have an ID."
            )

        if not source:

            errors.append(
                "Sequence flow "
                + str(flow_id)
                + " has no sourceRef."
            )

        elif source not in ids:

            errors.append(
                "Sequence flow "
                + str(flow_id)
                + " references an unknown source: "
                + source
            )

        if not target:

            errors.append(
                "Sequence flow "
                + str(flow_id)
                + " has no targetRef."
            )

        elif target not in ids:

            errors.append(
                "Sequence flow "
                + str(flow_id)
                + " references an unknown target: "
                + target
            )

        if source and target:

            pair = (source, target)

            if pair in flow_pairs:

                errors.append(
                    "Duplicate sequence flow connection: "
                    + source
                    + " -> "
                    + target
                )

            flow_pairs.add(pair)

    return sequence_flows, errors


# ==================================================
# 12. VALIDATE START AND END EVENTS
# ==================================================

def validate_events(flow_elements, sequence_flows):

    errors = []

    start_events = [

        element for element in flow_elements

        if element.tag == qname(
            BPMN_NAMESPACE,
            "startEvent"
        )

    ]

    end_events = [

        element for element in flow_elements

        if element.tag == qname(
            BPMN_NAMESPACE,
            "endEvent"
        )

    ]

    if len(start_events) != 1:

        errors.append(
            "The process must contain exactly one start event."
        )

    if len(end_events) < 1:

        errors.append(
            "The process must contain at least one end event."
        )

    incoming = {}

    outgoing = {}

    for element in flow_elements:

        element_id = element.get("id")

        incoming[element_id] = []

        outgoing[element_id] = []

    for flow in sequence_flows:

        source = flow.get("sourceRef")

        target = flow.get("targetRef")

        if source in outgoing:

            outgoing[source].append(flow)

        if target in incoming:

            incoming[target].append(flow)

    for element in start_events:

        element_id = element.get("id")

        if incoming.get(element_id):

            errors.append(
                "Start event "
                + str(element_id)
                + " must not have incoming sequence flows."
            )

        if not outgoing.get(element_id):

            errors.append(
                "Start event "
                + str(element_id)
                + " must have an outgoing sequence flow."
            )

    for element in end_events:

        element_id = element.get("id")

        if outgoing.get(element_id):

            errors.append(
                "End event "
                + str(element_id)
                + " must not have outgoing sequence flows."
            )

        if not incoming.get(element_id):

            errors.append(
                "End event "
                + str(element_id)
                + " must have an incoming sequence flow."
            )

    return incoming, outgoing, errors


# ==================================================
# 13. VALIDATE GATEWAYS
# ==================================================

def validate_gateways(flow_elements, incoming, outgoing):

    errors = []

    for element in flow_elements:

        tag = element.tag.split("}")[-1]

        element_id = element.get("id")

        if tag == "exclusiveGateway":

            gateway_outgoing = outgoing.get(
                element_id,
                []
            )

            if len(gateway_outgoing) < 2:

                errors.append(
                    "Exclusive Gateway "
                    + str(element_id)
                    + " must have at least two outgoing flows."
                )

            for flow in gateway_outgoing:

                condition = flow.find(
                    qname(
                        BPMN_NAMESPACE,
                        "conditionExpression"
                    )
                )

                if (
                    condition is None
                    or not (condition.text or "").strip()
                ):

                    errors.append(
                        "Exclusive Gateway "
                        + str(element_id)
                        + " has an outgoing flow without a condition."
                    )

        elif tag == "parallelGateway":

            incoming_count = len(
                incoming.get(element_id, [])
            )

            outgoing_count = len(
                outgoing.get(element_id, [])
            )

            if (
                incoming_count < 2
                and outgoing_count < 2
            ):

                errors.append(
                    "Parallel Gateway "
                    + str(element_id)
                    + " must split or join multiple flows."
                )

    return errors


# ==================================================
# 14. VALIDATE BPMN DIAGRAM
# ==================================================

def validate_bpmn_diagram(root, process, ids):

    errors = []

    diagrams = root.findall(
        qname(
            BPMNDI_NAMESPACE,
            "BPMNDiagram"
        )
    )

    if not diagrams:

        errors.append(
            "BPMN diagram information is missing."
        )

        return errors

    plane = diagrams[0].find(
        qname(
            BPMNDI_NAMESPACE,
            "BPMNPlane"
        )
    )

    if plane is None:

        errors.append(
            "BPMNDiagram must contain a BPMNPlane."
        )

        return errors

    if plane.get("bpmnElement") != process.get("id"):

        errors.append(
            "BPMNPlane must reference the process ID."
        )

    shapes = plane.findall(
        qname(
            BPMNDI_NAMESPACE,
            "BPMNShape"
        )
    )

    edges = plane.findall(
        qname(
            BPMNDI_NAMESPACE,
            "BPMNEdge"
        )
    )

    shape_references = set()

    edge_references = set()

    for shape in shapes:

        reference = shape.get("bpmnElement")

        if reference not in ids:

            errors.append(
                "BPMNShape references an unknown element: "
                + str(reference)
            )

        shape_references.add(reference)

        bounds = shape.find(
            qname(
                DC_NAMESPACE,
                "Bounds"
            )
        )

        if bounds is None:

            errors.append(
                "BPMNShape "
                + str(shape.get("id"))
                + " is missing Bounds."
            )

    process_element_ids = {

        element.get("id")

        for element in process

        if element.tag != qname(
            BPMN_NAMESPACE,
            "sequenceFlow"
        )

    }

    for element_id in process_element_ids:

        if element_id not in shape_references:

            errors.append(
                "Missing BPMNShape for element: "
                + str(element_id)
            )

    for edge in edges:

        reference = edge.get("bpmnElement")

        if reference not in ids:

            errors.append(
                "BPMNEdge references an unknown element: "
                + str(reference)
            )

        edge_references.add(reference)

        waypoints = edge.findall(
            qname(
                DI_NAMESPACE,
                "waypoint"
            )
        )

        if len(waypoints) < 2:

            errors.append(
                "BPMNEdge "
                + str(edge.get("id"))
                + " must contain at least two waypoints."
            )

    for flow in process.findall(
        qname(
            BPMN_NAMESPACE,
            "sequenceFlow"
        )
    ):

        flow_id = flow.get("id")

        if flow_id not in edge_references:

            errors.append(
                "Missing BPMNEdge for sequence flow: "
                + str(flow_id)
            )

    return errors


# ==================================================
# 15. MAIN BPMN VALIDATION FUNCTION
# ==================================================

def validate_bpmn_xml(xml_content):

    all_errors = []

    # ----------------------------------------------
    # XML syntax validation
    # ----------------------------------------------

    root, errors = validate_xml_syntax(
        xml_content
    )

    if errors:

        return {
            "valid": False,
            "xsd_valid": False,
            "errors": errors
        }

    # ----------------------------------------------
    # Official BPMN 2.0 XSD validation
    # ----------------------------------------------

    xsd_errors = validate_bpmn_xsd(
        xml_content
    )

    all_errors.extend(xsd_errors)

    # ----------------------------------------------
    # Definitions validation
    # ----------------------------------------------

    all_errors.extend(
        validate_definitions(root)
    )

    # ----------------------------------------------
    # Process validation
    # ----------------------------------------------

    process, errors = validate_process(root)

    all_errors.extend(errors)

    if process is None:

        return {
            "valid": False,
            "xsd_valid": len(xsd_errors) == 0,
            "errors": all_errors
        }

    # ----------------------------------------------
    # Element ID validation
    # ----------------------------------------------

    ids, errors = validate_element_ids(
        root
    )

    all_errors.extend(errors)

    # ----------------------------------------------
    # Flow element validation
    # ----------------------------------------------

    flow_elements, errors = validate_flow_elements(
        process
    )

    all_errors.extend(errors)

    # ----------------------------------------------
    # Sequence flow validation
    # ----------------------------------------------

    sequence_flows, errors = validate_sequence_flows(
        process,
        ids
    )

    all_errors.extend(errors)

    # ----------------------------------------------
    # Event validation
    # ----------------------------------------------

    incoming, outgoing, errors = validate_events(
        flow_elements,
        sequence_flows
    )

    all_errors.extend(errors)

    # ----------------------------------------------
    # Gateway validation
    # ----------------------------------------------

    all_errors.extend(
        validate_gateways(
            flow_elements,
            incoming,
            outgoing
        )
    )

    # ----------------------------------------------
    # Diagram validation
    # ----------------------------------------------

    all_errors.extend(
        validate_bpmn_diagram(
            root,
            process,
            ids
        )
    )

    # ----------------------------------------------
    # Final result
    # ----------------------------------------------

    return {
        "valid": len(all_errors) == 0,
        "xsd_valid": len(xsd_errors) == 0,
        "errors": all_errors
    }