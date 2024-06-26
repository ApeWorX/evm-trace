from collections.abc import Iterator
from typing import TYPE_CHECKING, Optional, Union, cast

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address

from evm_trace.enums import CallType

if TYPE_CHECKING:
    from evm_trace.base import CallTreeNode, EventNode


def get_tree_display(call: "CallTreeNode") -> str:
    return "\n".join([str(t) for t in TreeRepresentation.make_tree(call)])


class TreeRepresentation:
    """
    A class for creating a simple tree-representation of a call-tree node.

    **NOTE**: We purposely are not using the rich library here to keep
    evm-trace small and simple while sill offering a nice stringified
    version of a :class:`~evm_trace.base.CallTreeNode`.
    """

    MIDDLE_PREFIX = "├──"
    LAST_PREFIX = "└──"
    PARENT_PREFIX_MIDDLE = "    "
    PARENT_PREFIX_LAST = "│   "

    def __init__(
        self,
        call: Union["CallTreeNode", "EventNode"],
        parent: Optional["TreeRepresentation"] = None,
        is_last: bool = False,
    ):
        self.call = call
        self.parent = parent
        self.is_last = is_last

    @property
    def depth(self) -> int:
        """
        The depth in the call tree, such as the
        number of calls deep.
        """
        return self.call.depth

    @property
    def title(self) -> str:
        """
        The title of the node representation, including address, calldata, and return-data.
        For event-nodes, it is mostly the selector string.
        """
        call_type = self.call.call_type.value

        if hasattr(self.call, "selector"):
            # Is an Event-node
            selector = self.call.selector.hex() if self.call.selector else None
            return f"{call_type}: {selector}"
        # else: Is a CallTreeNode

        address_hex_str = self.call.address.hex() if self.call.address else None
        try:
            address = to_checksum_address(address_hex_str) if address_hex_str else None
        except (ImportError, ValueError):
            # Ignore checksumming if user does not have eth-hash backend installed.
            address = cast(ChecksumAddress, address_hex_str)

        cost = self.call.gas_cost
        call_path = str(address) if address and int(address, 16) else ""
        if self.call.calldata:
            call_path = call_path or ""

            if (
                CallType.CREATE.value in self.call.call_type.value
                or self.call.call_type == CallType.SELFDESTRUCT
            ):
                # No method ID needed, the call-type prefix is clear enough.
                method_id = ""

            else:
                hex_id = self.call.calldata[:4].hex()
                method_id = f"<{hex_id}>" if hex_id else ""

            sep = "." if call_path and method_id else ""
            call_path = f"{call_path}{sep}{method_id}"

        call_path = (
            f"[reverted] {call_path}" if self.call.failed and self.parent is None else call_path
        )
        call_path = call_path.strip()
        node_title = f"{call_type}: {call_path}" if call_path else call_type
        if cost is not None:
            node_title = f"{node_title} [{cost} gas]"

        return node_title

    @classmethod
    def make_tree(
        cls,
        root: Union["CallTreeNode", "EventNode"],
        parent: Optional["TreeRepresentation"] = None,
        is_last: bool = False,
    ) -> Iterator["TreeRepresentation"]:
        """
        Create a node representation object from a :class:`~evm_trace.base.CallTreeNode`.

        Args:
            root (:class:`~evm_trace.base.CallTreeNode` | :class:`~evm_trace.base.EventNode`):
              The call-tree node or event-node to display.
            parent (Optional[:class:`~evm_trace.display.TreeRepresentation`]): The parent
              node of this node.
            is_last (bool): True if a leaf-node.
        """
        displayable_root = cls(root, parent=parent, is_last=is_last)
        yield displayable_root
        if hasattr(root, "topics"):
            # Events have no children.
            return

        # Handle events, which won't have any sub-calls or anything.
        total_events = len(root.events)
        for index, event in enumerate(root.events, start=1):
            is_last = index == total_events
            yield cls(event, parent=displayable_root, is_last=is_last)

        # Handle calls (and calls of calls).
        total_calls = len(root.calls)
        for index, child_node in enumerate(root.calls, start=1):
            is_last = index == total_calls
            # NOTE: `.make_tree()` will handle calls of calls (recursion).
            yield from cls.make_tree(child_node, parent=displayable_root, is_last=is_last)

    def __str__(self) -> str:
        """
        The representation str via ``calling str()``.
        """
        if self.parent is None:
            return self.title

        tree_prefix = self.LAST_PREFIX if self.is_last else self.MIDDLE_PREFIX
        parts = [f"{tree_prefix} {self.title}"]
        parent = self.parent
        while parent and parent.parent is not None:
            parts.append(self.PARENT_PREFIX_MIDDLE if parent.is_last else self.PARENT_PREFIX_LAST)
            parent = parent.parent

        return "".join(reversed(parts))

    def __repr__(self) -> str:
        return str(self)
