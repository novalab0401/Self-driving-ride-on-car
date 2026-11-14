import os
import xml.etree.ElementTree as ET

from . import bt_nodes


def build_behavior_tree(shared_node, behavior_tree_xml: str):
    """BT XML 파일(Groot2 로 편집)을 읽어 트리를 만들고 루트 노드를 돌려준다.

    shared_node : 모든 BT 노드가 함께 쓰는 ROS2 노드 (구독 데이터, 퍼블리셔)
    """
    bt_root = ET.parse(behavior_tree_xml).getroot().find("BehaviorTree")
    if bt_root is None:
        raise ValueError("[BT ERROR] <BehaviorTree> tag not found in XML.")

    return _parse_xml_node(bt_root, shared_node=shared_node, top_xml_path=behavior_tree_xml)


def convert_value(v):
    """XML 속성 문자열을 값으로 바꾼다: "None" -> None, "123" -> int, "1.23" -> float."""
    if v == "None":
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def _parse_xml_node(xml_node, *, shared_node, top_xml_path):
    node_type = xml_node.tag

    # SubTree: 같은 폴더의 <ID>.xml 을 읽어 그 자리에 넣는다
    if node_type == "SubTree":
        subtree_id = xml_node.attrib.get("ID")
        if not subtree_id:
            raise ValueError("[BT ERROR] <SubTree> must have an ID attribute.")

        base_dir = os.path.dirname(os.path.abspath(top_xml_path))
        subtree_xml_path = os.path.join(base_dir, f"{subtree_id}.xml")
        subtree_root = ET.parse(subtree_xml_path).getroot().find("BehaviorTree")
        if subtree_root is None:
            raise ValueError(f"[BT ERROR] SubTree file '{subtree_id}.xml' has no <BehaviorTree>.")

        return _parse_xml_node(subtree_root, shared_node=shared_node, top_xml_path=subtree_xml_path)

    children = [
        _parse_xml_node(child, shared_node=shared_node, top_xml_path=top_xml_path)
        for child in xml_node
    ]

    if node_type == "BehaviorTree":
        if not children:
            raise ValueError("[BT ERROR] <BehaviorTree> has no child.")
        return children[0]

    # '_' 로 시작하는 속성은 Groot2 가 쓰는 메모용이라 노드에 넘기지 않는다.
    # name 은 Groot2 에서 노드에 붙인 별칭이므로 노드 이름으로 쓴다.
    attrib = {k: convert_value(v) for k, v in xml_node.attrib.items() if not k.startswith("_")}
    name = str(attrib.pop("name", node_type))

    BTNodeList = bt_nodes.BTNodeList

    if node_type in BTNodeList.CONTROL_NODES:
        return getattr(bt_nodes, node_type)(name=name, children=children, **attrib)

    if node_type in BTNodeList.DECORATOR_NODES:
        if len(children) != 1:
            raise ValueError(f"[BT ERROR] Decorator '{node_type}' must have exactly one child.")
        return getattr(bt_nodes, node_type)(name=name, child=children[0], **attrib)

    if node_type in (BTNodeList.ACTION_NODES + BTNodeList.CONDITION_NODES):
        return getattr(bt_nodes, node_type)(name=name, shared=shared_node, **attrib)

    raise ValueError(f"[BT ERROR] Unknown BT node type: {node_type}")
