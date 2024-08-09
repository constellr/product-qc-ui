import json
import requests
import streamlit as st


# ARGO_SERVER_ADDRESS = "http://argo.test.software.internal"
ARGO_SERVER_ADDRESS = "http://argo.product.internal"


@st.cache_data
def list_workflows(namespace: str, workflow_template_name: str = 'lst30-pipeline-v0.1.0'):
    """List all workflows in a specific namespace."""
    list_url = f"{ARGO_SERVER_ADDRESS}/api/v1/workflows/{namespace}"
    
    headers = {"Content-Type": "application/json"}
    response = requests.get(list_url, headers=headers)
    response.raise_for_status()
    
    response_json = response.json()
    workflows = response_json["items"]

    workflow_names = [wf["metadata"]["name"] for wf in workflows if wf["metadata"]["labels"]["workflows.argoproj.io/workflow-template"] == workflow_template_name]
    return workflow_names