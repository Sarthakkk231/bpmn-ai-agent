
import json
import streamlit as st

import agent as bpmn_agent
import bpmn_generator
import bpmn_validator


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="BPMN AI Agent",
    page_icon="🤖",
    layout="wide"
)


# ==================================================
# 2. CUSTOM STYLING
# ==================================================

st.markdown("""
<style>

.main-title {
    font-size: 32px;
    font-weight: 700;
    color: #1F4E79;
}

.subtitle {
    color: #777777;
    font-size: 15px;
}

.stChatMessage {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. SESSION STATE
# ==================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []


# ==================================================
# 4. SIDEBAR
# ==================================================

with st.sidebar:

    st.title("BPMN AI Agent")

    st.caption("AI-powered business process assistant")

    st.divider()

    st.subheader("Model Information")

    st.write("**Model:** Qwen 2.5 3B")
    st.write("**Framework:** LangChain")
    st.write("**LLM Runtime:** Ollama")

    st.divider()

    st.subheader("Available Features")

    st.markdown("""
    - BPMN concept explanations
    - AI and automation questions
    - BPMN workflow generation
    - JSON structure validation
    - BPMN XML generation
    - BPMN XML structural validation
    - JSON and XML downloads
    """)

    st.divider()

    if st.button("Clear Chat", use_container_width=True):

        st.session_state.messages = []
        st.session_state.agent_messages = []

        st.rerun()


# ==================================================
# 5. MAIN HEADER
# ==================================================

st.markdown(
    '<div class="main-title">BPMN AI Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Generate BPMN workflows and explore business process automation.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ==================================================
# 6. WELCOME MESSAGE
# ==================================================

if not st.session_state.messages:

    st.markdown("### Welcome!")

    st.write(
        "I am your BPMN AI assistant. "
        "You can ask me BPMN questions, explore AI concepts, "
        "or generate structured BPMN workflows."
    )

    


# ==================================================
# 7. DISPLAY CHAT HISTORY
# ==================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        message_type = message.get("type")

        # ------------------------------------------
        # BPMN GENERATION RESULT
        # ------------------------------------------

        if message_type == "bpmn_result":

            st.success("BPMN workflow generated successfully.")

            st.markdown("### BPMN JSON")

            st.json(message["data"])

            st.download_button(
                label="Download BPMN JSON",
                data=json.dumps(
                    message["data"],
                    indent=4
                ),
                file_name="bpmn_workflow.json",
                mime="application/json",
                key=message["json_download_key"]
            )

            # --------------------------------------
            # XML RESULT
            # --------------------------------------

            if message.get("xml_valid"):

                st.success("BPMN XML structural validation passed.")

                st.markdown("### BPMN XML")

                with st.expander("View generated BPMN XML"):

                    st.code(
                        message["xml_content"],
                        language="xml"
                    )

                st.download_button(
                    label="Download BPMN XML",
                    data=message["xml_content"],
                    file_name="bpmn_workflow.bpmn",
                    mime="application/xml",
                    key=message["xml_download_key"]
                )

                st.caption(
                    "XML file saved in generated_bpmn/"
                )

            else:

                st.error("BPMN XML validation failed.")

                st.markdown("**Validation errors:**")

                for error in message.get("xml_errors", []):
                    st.write("- " + str(error))

        # ------------------------------------------
        # BPMN GENERATION ERROR
        # ------------------------------------------

        elif message_type == "bpmn_error":

            st.error(message["content"])

            if message.get("data") is not None:

                st.markdown("**Generated JSON:**")

                st.json(message["data"])

        # ------------------------------------------
        # NORMAL CHAT MESSAGE
        # ------------------------------------------

        else:

            st.markdown(message["content"])


# ==================================================
# 8. CHAT INPUT
# ==================================================

user_input = st.chat_input(
    "Ask a BPMN or AI-related question..."
)


# ==================================================
# 9. PROCESS USER INPUT
# ==================================================

if user_input:

    # ----------------------------------------------
    # DISPLAY USER MESSAGE
    # ----------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # ----------------------------------------------
    # GENERATE ASSISTANT RESPONSE
    # ----------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("AI Agent is thinking..."):

            try:

                # ==================================
                # BPMN GENERATION REQUEST
                # ==================================

                if bpmn_agent.is_bpmn_generation_request(user_input):

                    # ----------------------------------
                    # STEP 1: GENERATE BPMN JSON
                    # ----------------------------------

                    result = bpmn_agent.generate_and_validate(
                        user_input
                    )

                    if result.startswith("BPMN_VALIDATION_PASSED"):

                        json_text = result.split(
                            "\n\n",
                            1
                        )[1]

                        bpmn_data = json.loads(json_text)

                        st.success(
                            "BPMN JSON generated and validated!"
                        )

                        st.markdown("### BPMN JSON")

                        st.json(bpmn_data)

                        # ----------------------------------
                        # STEP 2: GENERATE BPMN XML
                        # ----------------------------------

                        st.markdown("### Generating BPMN XML")

                        xml_content = (
                            bpmn_generator.generate_bpmn_xml(
                                bpmn_data
                            )
                        )

                        # ----------------------------------
                        # STEP 3: VALIDATE BPMN XML
                        # ----------------------------------

                        validation_result = (
                            bpmn_validator.validate_bpmn_xml(
                                xml_content
                            )
                        )

                        xml_valid = validation_result["valid"]

                        xml_errors = validation_result["errors"]

                        # ----------------------------------
                        # STEP 4: DISPLAY XML RESULT
                        # ----------------------------------

                        if xml_valid:

                            st.success(
                                "BPMN XML structural validation passed!"
                            )

                            with st.expander(
                                "View generated BPMN XML"
                            ):

                                st.code(
                                    xml_content,
                                    language="xml"
                                )

                            # Save XML file locally.

                            bpmn_generator.save_bpmn_xml(
                                xml_content,
                                "bpmn_workflow.bpmn"
                            )

                            st.caption(
                                "BPMN XML saved in generated_bpmn/"
                            )

                        else:

                            st.error(
                                "BPMN XML validation failed."
                            )

                            st.markdown("**Validation errors:**")

                            for error in xml_errors:
                                st.write("- " + str(error))

                        # ----------------------------------
                        # STEP 5: DOWNLOAD OPTIONS
                        # ----------------------------------

                        message_number = len(
                            st.session_state.messages
                        )

                        json_download_key = (
                            "json_download_"
                            + str(message_number)
                        )

                        xml_download_key = (
                            "xml_download_"
                            + str(message_number)
                        )

                        st.download_button(
                            label="Download BPMN JSON",
                            data=json.dumps(
                                bpmn_data,
                                indent=4
                            ),
                            file_name="bpmn_workflow.json",
                            mime="application/json",
                            key=json_download_key
                        )

                        if xml_valid:

                            st.download_button(
                                label="Download BPMN XML",
                                data=xml_content,
                                file_name="bpmn_workflow.bpmn",
                                mime="application/xml",
                                key=xml_download_key
                            )

                        # ----------------------------------
                        # STEP 6: SAVE RESULT IN CHAT HISTORY
                        # ----------------------------------

                        st.session_state.messages.append({

                            "role": "assistant",

                            "type": "bpmn_result",

                            "data": bpmn_data,

                            "xml_content": xml_content,

                            "xml_valid": xml_valid,

                            "xml_errors": xml_errors,

                            "json_download_key": json_download_key,

                            "xml_download_key": xml_download_key

                        })

                    else:

                        st.error(result)

                        st.session_state.messages.append({

                            "role": "assistant",

                            "type": "bpmn_error",

                            "content": result

                        })

                # ==================================
                # NORMAL AI / BPMN QUESTIONS
                # ==================================

                else:

                    st.session_state.agent_messages.append({

                        "role": "user",

                        "content": user_input

                    })

                    response = bpmn_agent.agent.invoke({

                        "messages": st.session_state.agent_messages

                    })

                    st.session_state.agent_messages = (
                        response["messages"]
                    )

                    final_response = (
                        st.session_state.agent_messages[-1].content
                    )

                    if not isinstance(final_response, str):

                        final_response = str(final_response)

                    st.markdown(final_response)

                    st.session_state.messages.append({

                        "role": "assistant",

                        "content": final_response

                    })

            except Exception as error:

                error_message = (
                    "Something went wrong: " + str(error)
                )

                st.error(error_message)

                st.session_state.messages.append({

                    "role": "assistant",

                    "content": error_message

                })
