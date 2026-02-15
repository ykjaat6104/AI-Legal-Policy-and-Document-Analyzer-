from langgraph.graph import StateGraph, END
from .workflow_nodes import LegalNodes, GraphState

def create_workflow():
    # build processing graph
    nodes = LegalNodes()
    workflow = StateGraph(GraphState)
    
    # define nodes
    workflow.add_node("retrieve", nodes.retrieve)
    workflow.add_node("analyze_risk", nodes.analyze_risk)
    workflow.add_node("generate_answer", nodes.generate_answer)
    
    # define path
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "analyze_risk")
    workflow.add_edge("analyze_risk", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    return workflow.compile()
