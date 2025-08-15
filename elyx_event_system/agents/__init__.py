from .ruby import ruby_node
from .dr_warren import drwarren_node
from .advik import advik_node
from .carla import carla_node
from .rachel import rachel_node
from .neel import neel_node

AGENT_KEYS = ["Ruby", "DrWarren", "Advik", "Carla", "Rachel", "Neel"]

AGENT_NODE_MAP = {
    "Ruby": "RubyNode",
    "DrWarren": "DrWarrenNode",
    "Advik": "AdvikNode",
    "Carla": "CarlaNode",
    "Rachel": "RachelNode",
    "Neel": "NeelNode"
}

AGENT_FUNC_MAP = {
    "Ruby": ruby_node,
    "DrWarren": drwarren_node,
    "Advik": advik_node,
    "Carla": carla_node,
    "Rachel": rachel_node,
    "Neel": neel_node
}