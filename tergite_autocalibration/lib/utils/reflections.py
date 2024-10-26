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
import importlib.util
import os
from pathlib import Path
from typing import Union


def import_class_from_file(class_name: str, file_path: Union[str, Path]):
    """
    Imports a class from a given file path.

    Args:
        class_name (str): The name of the class to import.
        file_path (str): The path to the file containing the class.

    Returns:
        type: The class type if found, otherwise raises an AttributeError or FileNotFoundError.
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
):
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

    return inheriting_classes
