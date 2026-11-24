
import json
import re

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_ollama import ChatOllama


# ==================================================
# 1. MODEL CONFIGURATION
# ==================================================

MODEL_NAME = "qwen2.5:3b"

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0,
    num_ctx=4096,
    num_predict=2500
)


# ==================================================
# 2. BPMN KNOWLEDGE TOOL
# ==================================================

@tool
def get_bpmn_element_info(element_name: str) -> str:
    """Explain common BPMN elements."""

    bpmn_elements = {
        "start event": (
            "A Start Event indicates where a BPMN process begins. "
            "It has no incoming sequence flow."
        ),
        "end event": (
            "An End Event indicates where a BPMN process terminates. "
            "It has no outgoing sequence flow."
        ),
        "task": (
            "A Task represents an activity performed within a process."
        ),
        "user task": (
            "A User Task represents work performed by a human participant."
        ),
        "service task": (
            "A Service Task represents an automated activity performed "
            "by a system or application."
        ),
        "exclusive gateway": (
            "An Exclusive Gateway represents a decision point. "
            "Only one outgoing path is selected based on conditions."
        ),
        "parallel gateway": (
            "A Parallel Gateway splits a process into paths that execute "
            "simultaneously, or synchronizes parallel paths."
        ),
        "sequence flow": (
            "A Sequence Flow connects BPMN elements and defines "
            "the order in which they execute."
        )
    }

    search_term = element_name.lower().strip()

    for element, description in bpmn_elements.items():

        if search_term == element or search_term in element:
            return description

    return (
        "Element not found. Available elements: "
        + ", ".join(bpmn_elements.keys())
    )


# ==================================================
# 3. JSON EXTRACTION
# ==================================================

def extract_json(text):
    """Extract the first complete JSON object from a model response."""

    text = str(text).strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\s*```$", "", text)

    start_index = text.find("{")

    if start_index == -1:
        raise ValueError("No JSON object found in model response.")

    decoder = json.JSONDecoder()

    data, end_index = decoder.raw_decode(text[start_index:])

    if not isinstance(data, dict):
        raise ValueError("Generated JSON must be an object.")

    return data


# ==================================================
# 4. NORMALIZATION HELPERS
# ==================================================

def make_identifier(value, prefix="Element"):

    identifier = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        str(value)
    ).strip("_")

    if not identifier:
        identifier = prefix

    if not identifier[0].isalpha():
        identifier = prefix + "_" + identifier

    return identifier


def normalize_element_type(element):
    """
    Convert different element type representations
    into the canonical BPMN type.
    """

    raw_type = element.get("type")

    if not raw_type:
        raw_type = element.get("elementDefinition")

    if not raw_type:

        type_keys = {
            "startEvent": "start_event",
            "endEvent": "end_event",
            "userTask": "user_task",
            "serviceTask": "service_task",
            "exclusiveGateway": "exclusive_gateway",
            "parallelGateway": "parallel_gateway",
            "task": "task"
        }

        for key, value in type_keys.items():

            if key in element:
                raw_type = value
                break

    if not raw_type:
        return None

    value = re.sub(
        r"([a-z])([A-Z])",
        r"\1_\2",
        str(raw_type)
    )

    value = re.sub(
        r"[\s-]+",
        "_",
        value
    ).lower()

    aliases = {
        "startevent": "start_event",
        "start_event": "start_event",
        "endevent": "end_event",
        "end_event": "end_event",
        "usertask": "user_task",
        "user_task": "user_task",
        "servicetask": "service_task",
        "service_task": "service_task",
        "exclusivegateway": "exclusive_gateway",
        "exclusive_gateway": "exclusive_gateway",
        "parallelgateway": "parallel_gateway",
        "parallel_gateway": "parallel_gateway",
        "task": "task"
    }

    return aliases.get(value)


# ==================================================
# 5. NORMALIZE GENERATED BPMN JSON
# ==================================================

def normalize_bpmn_structure(data):
    """
    Normalize common LLM output variations into the
    canonical structure used by this application.

    Canonical format:

    {
        "process_name": "...",
        "elements": [],
        "sequence_flows": []
    }

    This function standardizes formatting.
    It does not invent missing business logic.
    """

    if not isinstance(data, dict):
        raise ValueError("Generated BPMN must be a JSON object.")

    normalized = {
        "process_name": data.get(
            "process_name",
            "Generated Process"
        ),
        "elements": [],
        "sequence_flows": []
    }

    raw_elements = data.get("elements", [])

    if not isinstance(raw_elements, list):
        raw_elements = []

    # ----------------------------------------------
    # Normalize elements
    # ----------------------------------------------

    for index, raw_element in enumerate(raw_elements):

        if not isinstance(raw_element, dict):
            continue

        element = dict(raw_element)

        element_id = element.get("id")
        element_name = element.get("name")

        if not element_name and element_id:
            element_name = str(element_id).replace("_", " ")

        if not element_id and element_name:
            element_id = make_identifier(element_name)

        element_type = normalize_element_type(element)

        # Remove alternative representations.

        for key in [
            "elementDefinition",
            "startEvent",
            "endEvent",
            "userTask",
            "serviceTask",
            "exclusiveGateway",
            "parallelGateway"
        ]:
            element.pop(key, None)

        element.pop("next", None)

        element["id"] = (
            str(element_id)
            if element_id
            else "Element_" + str(index + 1)
        )

        element["name"] = (
            str(element_name)
            if element_name
            else element["id"]
        )

        element["type"] = element_type

        normalized["elements"].append(element)

    # ----------------------------------------------
    # Merge separately generated end events
    # ----------------------------------------------

    raw_end_events = data.get("end_events", [])

    if isinstance(raw_end_events, list):

        for index, raw_end in enumerate(raw_end_events):

            if not isinstance(raw_end, dict):
                continue

            end_name = raw_end.get("name")
            end_id = raw_end.get("id")

            if not end_name and end_id:
                end_name = str(end_id).replace("_", " ")

            if not end_name:
                end_name = "End Event " + str(index + 1)

            if not end_id:
                end_id = make_identifier(end_name, "End")

            matching = None

            for element in normalized["elements"]:

                if (
                    element["name"].strip().lower()
                    == str(end_name).strip().lower()
                ):
                    matching = element
                    break

            if matching:

                matching["type"] = "end_event"

            else:

                normalized["elements"].append({
                    "id": str(end_id),
                    "type": "end_event",
                    "name": str(end_name)
                })

    # ----------------------------------------------
    # Normalize sequence flows
    # ----------------------------------------------

    raw_flows = data.get("sequence_flows")

    if raw_flows is None:
        raw_flows = data.get("sequenceFlows", [])

    if not isinstance(raw_flows, list):
        raw_flows = []

    for index, raw_flow in enumerate(raw_flows):

        if not isinstance(raw_flow, dict):
            continue

        source = raw_flow.get("from")

        if source is None:
            source = raw_flow.get("sourceId")

        if source is None:
            source = raw_flow.get("source")

        target = raw_flow.get("to")

        if target is None:
            target = raw_flow.get("targetId")

        if target is None:
            target = raw_flow.get("target")

        condition = raw_flow.get("condition")

        if condition is None:
            condition = raw_flow.get("conditionExpression")

        normalized["sequence_flows"].append({
            "id": str(
                raw_flow.get("id")
                or "Flow_" + str(index + 1)
            ),
            "from": str(source) if source is not None else "",
            "to": str(target) if target is not None else "",
            "condition": condition
        })

    # ----------------------------------------------
    # Convert element names in flows into IDs
    # ----------------------------------------------

    name_to_id = {}

    element_ids = set()

    for element in normalized["elements"]:

        name_to_id[
            element["name"].strip().lower()
        ] = element["id"]

        element_ids.add(element["id"])

    for flow in normalized["sequence_flows"]:

        source = flow["from"]
        target = flow["to"]

        if source not in element_ids:

            flow["from"] = name_to_id.get(
                source.strip().lower(),
                source
            )

        if target not in element_ids:

            flow["to"] = name_to_id.get(
                target.strip().lower(),
                target
            )

    # ----------------------------------------------
    # Add start event if missing
    # ----------------------------------------------

    starts = [
        element for element in normalized["elements"]
        if element.get("type") == "start_event"
    ]

    if not starts and normalized["elements"]:

        incoming_targets = set(
            flow["to"]
            for flow in normalized["sequence_flows"]
            if flow.get("to")
        )

        candidates = [
            element for element in normalized["elements"]
            if (
                element.get("type") != "end_event"
                and element["id"] not in incoming_targets
            )
        ]

        if candidates:

            existing_ids = set(
                element["id"]
                for element in normalized["elements"]
            )

            start_id = "Start_1"
            counter = 1

            while start_id in existing_ids:

                counter += 1
                start_id = "Start_" + str(counter)

            normalized["elements"].insert(0, {
                "id": start_id,
                "type": "start_event",
                "name": "Start"
            })

            normalized["sequence_flows"].insert(0, {
                "id": "Flow_Start",
                "from": start_id,
                "to": candidates[0]["id"],
                "condition": None
            })

    return normalized


# ==================================================
# 6. BUILD NEXT ARRAYS AUTOMATICALLY
# ==================================================

def build_next_arrays(data):
    """
    Generate every element's next array from sequence_flows.
    Sequence flows remain the single source of truth.
    """

    elements = data.get("elements", [])
    flows = data.get("sequence_flows", [])

    next_mapping = {}

    for element in elements:

        if isinstance(element, dict):

            element_id = element.get("id")

            if isinstance(element_id, str):
                next_mapping[element_id] = []

    for flow in flows:

        if not isinstance(flow, dict):
            continue

        source = flow.get("from")
        target = flow.get("to")

        if source in next_mapping:
            next_mapping[source].append(target)

    for element in elements:

        if not isinstance(element, dict):
            continue

        element_id = element.get("id")

        if element_id in next_mapping:
            element["next"] = next_mapping[element_id]

    return data


# ==================================================
# 7. GENERIC BPMN VALIDATOR
# ==================================================

def validate_bpmn_structure(data, process_description=""):

    errors = []

    if not isinstance(data, dict):
        return ["Generated output must be a JSON object."]

    required_keys = [
        "process_name",
        "elements",
        "sequence_flows"
    ]

    for key in required_keys:

        if key not in data:
            errors.append("Missing required key: " + key)

    if errors:
        return errors

    if not isinstance(data["process_name"], str):
        errors.append("process_name must be a string.")

    elements = data["elements"]
    flows = data["sequence_flows"]

    if not isinstance(elements, list):
        return ["elements must be a list."]

    if not isinstance(flows, list):
        return ["sequence_flows must be a list."]

    if not elements:
        return ["The process must contain elements."]

    valid_types = {
        "start_event",
        "end_event",
        "task",
        "user_task",
        "service_task",
        "exclusive_gateway",
        "parallel_gateway"
    }

    element_ids = set()
    element_lookup = {}

    # ----------------------------------------------
    # Validate elements
    # ----------------------------------------------

    for index, element in enumerate(elements):

        if not isinstance(element, dict):

            errors.append(
                "Element at position "
                + str(index)
                + " must be an object."
            )

            continue

        element_id = element.get("id")
        element_type = element.get("type")
        element_name = element.get("name")

        if not isinstance(element_id, str) or not element_id.strip():

            errors.append(
                "Element at position "
                + str(index)
                + " has an invalid ID."
            )

            continue

        if element_id in element_ids:

            errors.append(
                "Duplicate element ID: " + element_id
            )

        element_ids.add(element_id)
        element_lookup[element_id] = element

        if element_type not in valid_types:

            errors.append(
                "Invalid type for "
                + element_id
                + ": "
                + str(element_type)
            )

        if not isinstance(element_name, str) or not element_name.strip():

            errors.append(
                "Element "
                + element_id
                + " must have a valid name."
            )

    if errors:
        return errors

    # ----------------------------------------------
    # Initialize connection mappings
    # ----------------------------------------------

    adjacency = {
        element_id: []
        for element_id in element_ids
    }

    incoming = {
        element_id: []
        for element_id in element_ids
    }

    outgoing = {
        element_id: []
        for element_id in element_ids
    }

    flow_pairs = set()

    # ----------------------------------------------
    # Validate sequence flows
    # ----------------------------------------------

    for index, flow in enumerate(flows):

        if not isinstance(flow, dict):

            errors.append(
                "Sequence flow at position "
                + str(index)
                + " must be an object."
            )

            continue

        source = flow.get("from")
        target = flow.get("to")

        if source not in element_ids:

            errors.append(
                "Sequence flow has unknown source: "
                + str(source)
            )

            continue

        if target not in element_ids:

            errors.append(
                "Sequence flow has unknown target: "
                + str(target)
            )

            continue

        pair = (source, target)

        if pair in flow_pairs:

            errors.append(
                "Duplicate sequence flow: "
                + str(source)
                + " -> "
                + str(target)
            )

        flow_pairs.add(pair)

        adjacency[source].append(target)
        outgoing[source].append(flow)
        incoming[target].append(flow)

        if "condition" not in flow:
            flow["condition"] = None

    # ----------------------------------------------
    # Validate next arrays
    # ----------------------------------------------

    for element_id, element in element_lookup.items():

        expected_next = adjacency[element_id]
        actual_next = element.get("next", [])

        if not isinstance(actual_next, list):

            errors.append(
                "The next field must be a list for "
                + element_id
            )

        elif actual_next != expected_next:

            errors.append(
                "The next field does not match sequence flows for "
                + element_id
            )

    # ----------------------------------------------
    # Validate start and end events
    # ----------------------------------------------

    start_events = [
        element for element in elements
        if element["type"] == "start_event"
    ]

    end_events = [
        element for element in elements
        if element["type"] == "end_event"
    ]

    if len(start_events) != 1:

        errors.append(
            "The process must contain exactly one start event."
        )

    if len(end_events) < 1:

        errors.append(
            "The process must contain at least one end event."
        )

    for element in elements:

        element_id = element["id"]
        element_type = element["type"]

        if element_type == "start_event":

            if incoming[element_id]:
                errors.append(
                    "Start event "
                    + element_id
                    + " must not have incoming flows."
                )

            if not outgoing[element_id]:
                errors.append(
                    "Start event "
                    + element_id
                    + " must have an outgoing flow."
                )

        elif element_type == "end_event":

            if outgoing[element_id]:
                errors.append(
                    "End event "
                    + element_id
                    + " must not have outgoing flows."
                )

            if not incoming[element_id]:
                errors.append(
                    "End event "
                    + element_id
                    + " must have an incoming flow."
                )

        else:

            if not incoming[element_id]:
                errors.append(
                    "Element "
                    + element_id
                    + " has no incoming flow."
                )

            if not outgoing[element_id]:
                errors.append(
                    "Element "
                    + element_id
                    + " has no outgoing flow."
                )

    # ----------------------------------------------
    # Validate gateways
    # ----------------------------------------------

    for element in elements:

        element_type = element["type"]
        gateway_id = element["id"]

        if element_type == "exclusive_gateway":

            gateway_flows = outgoing[gateway_id]

            if len(gateway_flows) < 2:

                errors.append(
                    "Exclusive Gateway "
                    + gateway_id
                    + " must have at least two outgoing flows."
                )

            for flow in gateway_flows:

                condition = flow.get("condition")

                if (
                    not isinstance(condition, str)
                    or not condition.strip()
                ):

                    errors.append(
                        "Outgoing flow from Exclusive Gateway "
                        + gateway_id
                        + " must have a condition."
                    )

        elif element_type == "parallel_gateway":

            if (
                len(outgoing[gateway_id]) < 2
                and len(incoming[gateway_id]) < 2
            ):

                errors.append(
                    "Parallel Gateway "
                    + gateway_id
                    + " must split into or join at least two flows."
                )

    # ----------------------------------------------
    # Validate reachability
    # ----------------------------------------------

    if len(start_events) == 1:

        start_id = start_events[0]["id"]

        visited = set()
        stack = [start_id]

        while stack:

            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)

            for target in adjacency[current]:

                if target not in visited:
                    stack.append(target)

        for element_id in element_ids:

            if element_id not in visited:

                errors.append(
                    "Element "
                    + element_id
                    + " is not reachable from the start event."
                )

    # ----------------------------------------------
    # Check that every path can reach an end event
    # ----------------------------------------------

    def can_reach_end(element_id, visited_path=None):

        if visited_path is None:
            visited_path = set()

        if element_id in visited_path:
            return False

        if element_lookup[element_id]["type"] == "end_event":
            return True

        next_path = set(visited_path)
        next_path.add(element_id)

        targets = adjacency[element_id]

        if not targets:
            return False

        return all(
            can_reach_end(target, next_path)
            for target in targets
        )

    for element in elements:

        if element["type"] == "end_event":
            continue

        if (
            adjacency[element["id"]]
            and not can_reach_end(element["id"])
        ):

            errors.append(
                "At least one path from element "
                + element["id"]
                + " does not reach an end event."
            )

    return errors


# ==================================================
# 8. GENERATION PROMPT
# ==================================================

def create_generation_prompt(process_description):

    prompt = """
You are an expert BPMN workflow designer.

Convert the user's business-process description into
a BPMN intermediate JSON structure.

IMPORTANT: This is a GENERIC BPMN generator.

Do not assume that every process is an approval workflow.
Do not use fixed example activities or business rules.
Do not insert unrelated activities.

MODELLING RULES:

1. Include all activities explicitly described by the user.
2. Preserve the meaning and order of the user's instructions.
3. Do not invent business activities, decisions, conditions,
   approvals, rejections, or outcomes.
4. Do not assume an unspecified outcome.
5. If an outcome is unspecified, do not invent what happens next.
6. Use exactly one start_event.
7. Use one element for each distinct activity or event.
8. Use user_task for human activities.
9. Use service_task for automated system activities.
10. Use task when the activity type is unclear.
11. Use exclusive_gateway for exclusive decisions.
12. Use ONE gateway for each decision.
13. Never create separate gateways for decision outcomes.
14. Put branch conditions on outgoing sequence flows.
15. Every exclusive gateway must have at least two outgoing flows.
16. Every outgoing exclusive gateway flow must have a condition.
17. Use separate end events for distinct terminal outcomes
    when the process description supports them.
18. Every element must be connected through sequence_flows.
19. Use unique IDs without spaces.
20. Use IDs in sequence flow references, not element names.
21. Do not generate a next field. Python generates it automatically.

CANONICAL JSON FORMAT:

{
    "process_name": "Process Name",
    "elements": [
        {
            "id": "Start_1",
            "type": "start_event",
            "name": "Process Start"
        },
        {
            "id": "Task_1",
            "type": "user_task",
            "name": "A described activity"
        },
        {
            "id": "Gateway_1",
            "type": "exclusive_gateway",
            "name": "A described decision"
        },
        {
            "id": "End_1",
            "type": "end_event",
            "name": "A described outcome"
        }
    ],
    "sequence_flows": [
        {
            "id": "Flow_1",
            "from": "Start_1",
            "to": "Task_1",
            "condition": null
        },
        {
            "id": "Flow_2",
            "from": "Task_1",
            "to": "Gateway_1",
            "condition": null
        },
        {
            "id": "Flow_3",
            "from": "Gateway_1",
            "to": "End_1",
            "condition": "A condition stated by the user"
        }
    ]
}

Return exactly these top-level keys:
process_name, elements, sequence_flows.

Return valid JSON only.
Do not use Markdown fences.
Do not add explanations or comments.

USER'S BUSINESS-PROCESS DESCRIPTION:

""" + process_description + """

Return only the JSON object.
"""

    return prompt


# ==================================================
# 9. GENERATE AND VALIDATE BPMN
# ==================================================

def generate_and_validate(process_description):

    try:

        prompt = create_generation_prompt(process_description)

        print("\nGenerating BPMN structure...\n")

        # ------------------------------------------
        # Initial generation
        # ------------------------------------------

        response = llm.invoke(prompt)

        generated_output = response.content

        if not isinstance(generated_output, str):
            generated_output = str(generated_output)

        raw_data = extract_json(generated_output)

        data = normalize_bpmn_structure(raw_data)

        data = build_next_arrays(data)

        errors = validate_bpmn_structure(
            data,
            process_description
        )

        # ------------------------------------------
        # Automatic correction attempt
        # ------------------------------------------

        if errors:

            print("Initial validation failed.")
            print("Attempting one automatic correction...\n")

            repair_prompt = """
You are correcting an invalid BPMN intermediate JSON structure.

Fix the structural validation errors while preserving
the original business-process meaning.

Do not invent activities, decisions, conditions, or outcomes.

VALIDATION ERRORS:

""" + "\n".join(
                "- " + error for error in errors
            ) + """

PREVIOUS NORMALIZED JSON:

""" + json.dumps(data, indent=4) + """

ORIGINAL BUSINESS-PROCESS DESCRIPTION:

""" + process_description + """

CORRECTION RULES:

1. Return exactly process_name, elements, and sequence_flows.
2. Use canonical type values:
   start_event, end_event, task, user_task, service_task,
   exclusive_gateway, parallel_gateway.
3. Use exactly one start event.
4. Use one element for each distinct activity, event, or gateway.
5. Use one exclusive gateway for each exclusive decision.
6. Do not create separate gateways for branch outcomes.
7. Put branch conditions on outgoing gateway flows.
8. Every flow must use from, to, and condition.
9. Flow endpoints must be existing element IDs.
10. All elements must be connected and reachable from the start.
11. Every process path must reach an end event.
12. Do not generate next arrays.
13. Do not invent business rules.
14. Preserve the original business-process meaning.
15. Return valid JSON only without Markdown fences.

Return the corrected JSON object.
"""

            repair_response = llm.invoke(repair_prompt)

            repaired_output = repair_response.content

            if not isinstance(repaired_output, str):
                repaired_output = str(repaired_output)

            repaired_raw_data = extract_json(repaired_output)

            data = normalize_bpmn_structure(
                repaired_raw_data
            )

            data = build_next_arrays(data)

            errors = validate_bpmn_structure(
                data,
                process_description
            )

        # ------------------------------------------
        # Final result
        # ------------------------------------------

        if errors:

            return (
                "BPMN_VALIDATION_FAILED\n\n"
                "The workflow still has validation errors "
                "after one correction attempt:\n\n"
                + "\n".join(
                    str(index + 1) + ". " + error
                    for index, error in enumerate(errors)
                )
                + "\n\nNormalized Generated JSON:\n\n"
                + json.dumps(data, indent=4)
            )

        return (
            "BPMN_VALIDATION_PASSED\n\n"
            + json.dumps(data, indent=4)
        )

    except json.JSONDecodeError as error:

        return (
            "JSON_GENERATION_ERROR\n"
            "The model returned invalid JSON.\n"
            "Details: "
            + str(error)
        )

    except Exception as error:

        return (
            "BPMN_GENERATION_ERROR\n"
            + str(error)
        )


# ==================================================
# 10. LANGCHAIN GENERATION TOOL
# ==================================================

@tool
def generate_bpmn_structure(process_description: str) -> str:
    """Generate and validate a BPMN workflow from a business process."""

    return generate_and_validate(process_description)


# ==================================================
# 11. CREATE LANGCHAIN AGENT
# ==================================================

agent = create_agent(
    model=llm,
    tools=[
        get_bpmn_element_info,
        generate_bpmn_structure
    ],
    system_prompt="""
You are a helpful BPMN and AI assistant.

Your responsibilities:

1. Explain BPMN concepts.
2. Explain BPMN events, tasks, gateways and sequence flows.
3. Answer general questions about AI and automation.
4. Use get_bpmn_element_info when BPMN element information is needed.
5. Use generate_bpmn_structure when a user requests BPMN generation.
6. Do not invent tool results.
7. Explain validation errors clearly.
8. Never claim invalid BPMN JSON has passed validation.
"""
)


# ==================================================
# 12. DETECT GENERATION REQUESTS
# ==================================================

def is_bpmn_generation_request(user_input):

    text = user_input.lower()

    generation_verbs = [
        "create",
        "generate",
        "design",
        "build",
        "make",
        "convert"
    ]

    generation_terms = [
        "bpmn",
        "workflow",
        "process flow",
        "business process"
    ]

    has_generation_verb = any(
        verb in text for verb in generation_verbs
    )

    has_generation_term = any(
        term in text for term in generation_terms
    )

    return (
        has_generation_verb
        and has_generation_term
    )


# ==================================================
# 13. INTERACTIVE AI AGENT
# ==================================================

def run_agent():

    conversation = []

    print("\nBPMN AI Agent is ready.")

    print("You can ask BPMN questions, AI questions,")
    print("or request BPMN workflow generation.")

    print("\nType 'exit' to stop.\n")

    while True:

        user_input = input("You: ").strip()

        if user_input.lower() in [
            "exit",
            "quit",
            "stop"
        ]:

            print("\nAgent stopped.")
            break

        if not user_input:
            continue

        # ------------------------------------------
        # Direct BPMN generation routing
        # ------------------------------------------

        if is_bpmn_generation_request(user_input):

            result = generate_and_validate(user_input)

            print("Agent:\n")
            print(result)

            print("\n" + "-" * 60 + "\n")

        # ------------------------------------------
        # Normal AI and BPMN questions
        # ------------------------------------------

        else:

            conversation.append({
                "role": "user",
                "content": user_input
            })

            try:

                response = agent.invoke({
                    "messages": conversation
                })

                conversation = response["messages"]

                final_message = conversation[-1].content

                if not isinstance(final_message, str):
                    final_message = str(final_message)

                print("\nAgent:", final_message)

                print("\n" + "-" * 60 + "\n")

            except Exception as error:

                print("\nAgent error:", str(error))

                print()


# ==================================================
# 14. MAIN PROGRAM
# ==================================================

if __name__ == "__main__":

    print("\n====================================")
    print("          BPMN AI AGENT")
    print("====================================")

    run_agent()
