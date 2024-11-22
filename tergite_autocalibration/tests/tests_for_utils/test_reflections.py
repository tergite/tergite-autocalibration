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

from tergite_autocalibration.utils.reflections import ASTParser


def test_ast_parser_basic_init_attributes():
    class SampleClass:
        def __init__(self):
            self.a = 10
            self.b = "hello"
            self.c: int = 42  # Annotated assignment

    result = ASTParser.get_init_attribute_names(SampleClass)
    assert result == {"a", "b", "c"}


def test_ast_parser_no_init_or_attributes():
    class EmptyClass:
        pass

    class NoAttributesClass:
        def __init__(self):
            pass

    # Test for a class without an __init__ method
    result_empty = ASTParser.get_init_attribute_names(EmptyClass)
    assert result_empty == set()

    # Test for a class with an __init__ method but no attributes
    result_no_attributes = ASTParser.get_init_attribute_names(NoAttributesClass)
    assert result_no_attributes == set()
