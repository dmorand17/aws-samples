import logging

from constructs import IConstruct

logger = logging.getLogger(__name__)


def _get_indent(level: int) -> str:
    return "  " * level


def print_children(construct: IConstruct, level: int) -> None:
    logger.debug(f"{_get_indent(level)}type: {type(construct)}")
    logger.debug(f"{_get_indent(level)}path: {construct.node.path}")

    for child in construct.node.children:
        # print("Processing children")
        logger.debug(f"{_get_indent(level + 1)}construct: {child.node.id}")
        print_children(child, level + 1)
