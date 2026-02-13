from langgraph.graph import StateGraph, END
from ai_legal_analyzer.workflows.nodes import LegalNodes, GraphState

def create_workflow():
    nodes = LegalNodes()
    
    workflow = StateGraph(GraphState)
    
    # Add Nodes
    workflow.add_node("retrieve", nodes.retrieve)
    workflow.add_node("analyze_risk", nodes.analyze_risk)
    workflow.add_node("generate_answer", nodes.generate_answer)
    
    # Define Edges
    workflow.set_entry_point("retrieve")
    
    workflow.add_edge("retrieve", "analyze_risk")
    workflow.add_edge("analyze_risk", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    # Compile
    app = workflow.compile()
    return app

if __name__ == "__main__":
    # Test the graph compilation
    app = create_workflow()
    print("Graph compiled successfully.")
