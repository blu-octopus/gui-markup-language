from guiml.compiler import compile_instance
from guiml.graph import build_system_graph
from guiml.linter import lint_instance
from guiml.retrieval import retrieve_subgraph


def test_graph_and_lint_rewrite():
    g = build_system_graph("S")
    assert g["kind"] == "system"
    assert any(n["kind"] == "token" for n in g["nodes"])
    inst = {
        "kind": "instance",
        "root": {
            "component": "Grid",
            "children": [
                {
                    "component": "Column",
                    "tokens": {"color": "ui-background"},
                    "children": [{"component": "Button", "props": {"kind": "primary"}, "text": "Save"}],
                }
            ],
        },
    }
    sub = retrieve_subgraph(g, expected_components=["Grid", "Column", "Button"], expected_tokens=["background"])
    diags = lint_instance(inst, sub)
    assert any(d["code"] == "R5" for d in diags)
    tsx = compile_instance(inst)
    assert "from '@carbon/react'" in tsx
    assert "<Grid" in tsx
