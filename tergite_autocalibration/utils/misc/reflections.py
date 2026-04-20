# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import ast
import importlib.util
import inspect
import os
import textwrap
from pathlib import Path
from typing import Set, Type, Any, Dict, List, Union

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
    def get_init_attribute_names(cls: Type[Any]) -> Set[str]:
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
            Set[str]: The names of the attributes in __init__ as set

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


def get_class_attributes(
    file_path: Union[str, Path], class_name: str
) -> Dict[str, List[str]]:
    """
    Current implementation only supports to return lists, but can easily be extended.

    Args:
        file_path: Path to the file that contains the class.
        class_name: Name of the class to parse.

    Returns:
        A dictionary that maps the class attribute name to their values.

    """
    with open(file_path, "r") as file:
        tree = ast.parse(file.read(), filename=file_path)

    return_obj_: Dict[str, List[str]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            if isinstance(item.value, ast.List):
                                return_list_: List[str] = []
                                for list_element in item.value.elts:
                                    if isinstance(list_element, ast.Constant):
                                        return_list_.append(list_element.value)
                                return_obj_[target.id] = return_list_
    return return_obj_


def import_class_from_file(class_name: str, file_path: Union[str, Path]) -> Type:
    """
    Imports a class from a given file path.

    Args:
        class_name (str): The name of the class to import.
        file_path (str): The path to the file containing the class.

    Returns:
        Type: The class type if found, otherwise raises an AttributeError or FileNotFoundError.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No such file: '{file_path}'")

    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Retrieve the class from the module
    try:
        return getattr(module, class_name)
    except AttributeError:
        raise AttributeError(f"Class '{class_name}' not found in '{file_path}'")


def find_inheriting_classes_ast_recursive(
    directory: Union[str, Path], base_class_name: str = None
) -> dict:
    """
    Recursively finds all classes in a directory and its subdirectories that inherit
    from the specified base class using AST parsing.

    Args:
        directory (str): The root directory to search for classes.
        base_class_name (str): The name of the base class to check inheritance.

    Returns:
        dict: A dictionary where keys are file paths, and values are lists of class names
              inheriting from base_class_name.
    """
    inheriting_classes = {}

    # Recursively walk through the directory and its subdirectories
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                with open(filepath, "r", encoding="utf-8") as file:
                    # Parse the file content into an AST
                    tree = ast.parse(file.read(), filename=filename)

                # Analyze each class in the file
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if the class inherits from base_class_name
                        for base in node.bases:
                            if (
                                isinstance(base, ast.Name)
                                and base.id == base_class_name
                            ) or base_class_name is None:
                                inheriting_classes[node.name] = filepath
                                break

    # TODO: We could have this function be even more sophisticated by checking inheritances in the post-processing.
    #       One possible implementation could be to find the inheritance recursively on a simplified AST.
    #       E.g.:
    #       - In the loop above, for each class store the parent-class
    #       - Then represent the information as tree
    #       - Have an efficient tree-search algorithm that finds recursively finds the ancestors for the parent
    #       - Filter the results in the `inheriting_classes` variable

    return inheriting_classes
