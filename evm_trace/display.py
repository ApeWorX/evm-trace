from typing import TYPE_CHECKING, Iterator, Optional, cast

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address

if TYPE_CHECKING:
    from evm_trace.base import CallTreeNode


def get_tree_display(call: "CallTreeNode") -> str:
    return "\n".join([str(t) for t in TreeRepresentation.make_tree(call)])


class TreeRepresentation:
    FILE_MIDDLE_PREFIX = "├──"
    FILE_LAST_PREFIX = "└──"
    PARENT_PREFIX_MIDDLE = "    "
    PARENT_PREFIX_LAST = "│   "

    def __init__(
        self,
        call: "CallTreeNode",
        parent: Optional["TreeRepresentation"] = None,
        is_last: bool = False,
    ):
        self.call = call
        self.parent = parent
        self.is_last = is_last

    @property
    def depth(self) -> int:
        return self.call.depth

    @property
    def title(self) -> str:
        call_type = self.call.call_type.value
        address_hex_str = self.call.address.hex() if self.call.address else None

        try:
            address = to_checksum_address(address_hex_str) if address_hex_str else None
        except (ImportError, ValueError):
            # Ignore checksumming if user does not have eth-hash backend installed.
            address = cast(ChecksumAddress, address_hex_str)

        cost = self.call.gas_cost
        call_path = str(address) if address else ""
        if self.call.calldata:
            call_path = f"{call_path}." if call_path else ""
            call_path = f"{call_path}<{self.call.calldata[:4].hex()}>"

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
        root: "CallTreeNode",
        parent: Optional["TreeRepresentation"] = None,
        is_last: bool = False,
    ) -> Iterator["TreeRepresentation"]:
        displayable_root = cls(root, parent=parent, is_last=is_last)
        yield displayable_root

        count = 1
        for child_node in root.calls:
            is_last = count == len(root.calls)
            if child_node.calls:
                yield from cls.make_tree(child_node, parent=displayable_root, is_last=is_last)
            else:
                yield cls(child_node, parent=displayable_root, is_last=is_last)

            count += 1

    def __str__(self) -> str:
        if self.parent is None:
            return self.title

        filename_prefix = self.FILE_LAST_PREFIX if self.is_last else self.FILE_MIDDLE_PREFIX

        parts = [f"{filename_prefix} {self.title}"]
        parent = self.parent
        while parent and parent.parent is not None:
            parts.append(self.PARENT_PREFIX_MIDDLE if parent.is_last else self.PARENT_PREFIX_LAST)
            parent = parent.parent

        return "".join(reversed(parts))
