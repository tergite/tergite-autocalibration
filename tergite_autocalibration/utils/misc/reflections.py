# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import ast
import inspect
import textwrap
from typing import Set

from tergite_autocalibration.utils.logging import logger


class ASTParser:
    """
    Parser for the abstract syntax tree. This is to allow inferring more information from
    the sourcecode itself.
    """

    @staticmethod
    def _get_source_tree_for_cls(cls) -> tuple:
        """
        Helper function to parse the source code of a class

        Args:
            cls: Class to be parsed as AST

        Returns:
            source

        """
        try:
            # Try to get the source code of the class
            source = inspect.getsource(cls)
            # Dedent the source to handle indented classes
            source = textwrap.dedent(source)
        except (TypeError, OSError, IndentationError) as e:
            # Handle errors in retrieving the source
            logger.info(f"Error retrieving source for {cls.__name__}: {e}")
            source = None

        try:
            # Parse the source code into an AST
            tree = ast.parse(source)
        except SyntaxError as e:
            # Handle parsing errors
            logger.info(f"Syntax error when parsing source of {cls.__name__}: {e}")
            tree = None

        return source, tree

    @staticmethod
    def get_init_attribute_names(cls) -> Set[str]:
        """
        Returns all the attributes from the __init__ function of a class

        Examples:
            >>> class MyClass:
            >>>
            >>>     def __init__(self):
            >>>         self.attr1 = 1
            >>>         self.attr2: str = "hello"
            >>>
            >>> init_attributes = ASTParser.get_init_attribute_names(MyClass)
            >>> logger.info(init_attributes)
            {'attr1', 'attr2'}

        Args:
            cls: Class to be analysed

        Returns:
            The names of the attributes in __init__ as set

        """

        # Parse source and tree for class definition
        source, tree = ASTParser._get_source_tree_for_cls(cls)

        # Find the class definition
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == cls.__name__:
                # Look for the __init__ method
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                        # Collect all assignments to 'self.<attribute>'
                        attributes = set()
                        for stmt in child.body:
                            # Handle `Assign`, this is for normal variables e.g. self.var1 = 0
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if (
                                        isinstance(target, ast.Attribute)
                                        and isinstance(target.value, ast.Name)
                                        and target.value.id == "self"
                                    ):
                                        attributes.add(target.attr)
                            # Handle `AnnAssign`, this is for annotated variables e.g. self.var1: int = 0
                            elif isinstance(stmt, ast.AnnAssign):
                                if (
                                    isinstance(stmt.target, ast.Attribute)
                                    and isinstance(stmt.target.value, ast.Name)
                                    and stmt.target.value.id == "self"
                                ):
                                    attributes.add(stmt.target.attr)
                        return attributes
        return set()
