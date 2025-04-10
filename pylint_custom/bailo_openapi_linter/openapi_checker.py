"""Pylint custom checker to compare the Bailo Python client with Bailo's backend OpenAPI specification."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import requests
from astroid import nodes
from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from pylint.lint import PyLinter


class OpenAPISpecChecker(BaseChecker):
    """Compare the Bailo Python client implementation's coverage of the OpenAPI spec."""

    name = "OpenAPISpecCoverage"
    msgs = {
        "W9001": ("Endpoint not covered: %s", "endpoint-not-covered", ""),
        "E9001": ("Endpoint not found in specification: %s", "endpoint-unknown", ""),
    }

    def __init__(self, linter: PyLinter | None = None) -> None:
        if linter:
            super().__init__(linter)
        r = requests.get(
            "http://localhost:8080/api/v2/specification", headers={"Accept": "application/json"}, timeout=5
        )
        self._openapi_response = r.json()
        self.paths_to_check = {}
        for path in self._openapi_response.get("paths").keys():
            http_methods = self._openapi_response.get("paths")[path].keys()
            formatted_path = re.sub(r"{[^}]*}", "*", path)
            for http_method in http_methods:
                self.paths_to_check[f"{http_method}:{formatted_path}"] = False

    def visit_call(self, node: nodes.Call):
        """Check if a Call node matches `self.agent.<method>(<url>)` and update the dict of found endpoints accordingly.

        :param node: Call node to check.
        """
        # Check Call matches `self.agent.<method>(<url>)`
        if (
            isinstance(node.func, nodes.Attribute)
            and isinstance(node.func.expr, nodes.Attribute)
            and node.func.expr.repr_name() == "agent"
            and node.func.expr.expr.repr_name() == "self"
        ):
            http_method = node.func.repr_name()
            for arg in node.args:
                if isinstance(arg, nodes.JoinedStr):
                    # format endpoint to match openapi spec
                    path = "".join(
                        [
                            (
                                "/api"
                                if index == 0 and isinstance(arg_part, nodes.FormattedValue)
                                else arg_part.value if isinstance(arg_part, nodes.Const) else "*"
                            )
                            for index, arg_part in enumerate(arg.values)
                        ]
                    )
                    path_to_check = f"{http_method}:{path}"
                    if path_to_check in self.paths_to_check:
                        # update endpoint dict
                        self.paths_to_check[path_to_check] = True
                    else:
                        # unknown endpoint found
                        self.add_message("endpoint-unknown", node=node, args=path_to_check)

    def leave_module(self, node: nodes.Module) -> None:
        """Check if the module was the expected one, and if so list the endpoints that were not found.

        :param node: Module to check.
        """
        if node.repr_name() == "bailo.core.client":
            for path in [path for path, covered in self.paths_to_check.items() if not covered]:
                self.add_message("endpoint-not-covered", node=node, args=path)


def register(linter: PyLinter) -> None:
    """This required method auto registers the checker during initialization.

    :param linter: The linter to register the checker to.
    """
    linter.register_checker(OpenAPISpecChecker(linter))
