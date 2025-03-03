# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

import pytest
import yaml

from pyavd._schema.models.avd_base import AvdBase
from pyavd._schema.models.avd_indexed_list import AvdIndexedList
from pyavd._schema.models.avd_list import AvdList
from pyavd._schema.models.avd_model import AvdModel
from pyavd._schema.models.input_path import InputPath
from pyavd._utils import Undefined
from schema_tools.generate_classes.src_generators import FileSrc
from schema_tools.metaschema.meta_schema_model import AristaAvdSchema

if TYPE_CHECKING:
    from .data_merging_schema_class import DataMergingTestSchema


script_dir = Path(__file__).parent


@pytest.fixture(scope="module")
def data_merging_schema_class() -> DataMergingTestSchema:
    with Path(script_dir, "data_merging.schema.yml").open(encoding="utf-8") as schema_file:
        raw_schema = yaml.load(schema_file, Loader=yaml.CSafeLoader)

    schema = AristaAvdSchema(**raw_schema)
    schemasrc = schema._generate_class_src(class_name="DataMergingTestSchema")
    src_file_contents = FileSrc(classes=[schemasrc.cls])

    # Writing to file to assist the type-checker for these tests.
    with Path(script_dir, "data_merging_schema_class.py").open(mode="w", encoding="UTF-8") as file:
        file.write(str(src_file_contents))

    cls_module = module_from_spec(ModuleSpec(name="cls_module", loader=None))
    exec(str(src_file_contents), cls_module.__dict__)  # noqa: S102

    return cls_module.DataMergingTestSchema


A_LIST = {"some_list": [1, 2]}
B_LIST = {"some_list": [2, 3, 4]}
ALL_A_AND_B_LISTS = {"some_list": [1, 2, 2, 3, 4]}
UNIQUE_A_AND_B_LISTS = {"some_list": [1, 2, 3, 4]}
ALL_B_AND_A_LISTS = {"some_list": [2, 3, 4, 1, 2]}
UNIQUE_B_AND_A_LISTS = {"some_list": [3, 4, 1, 2]}

A_INDEXED_LIST = {"some_indexed_list": [{"name": "one", "some_int": 1}, {"name": "two", "some_int": 2}]}
B_INDEXED_LIST = {"some_indexed_list": [{"name": "two", "some_int": 2}, {"name": "three", "some_int": 3}, {"name": "four", "some_int": 4}]}
UNIQUE_A_AND_B_INDEXED_LISTS = {
    "some_indexed_list": [{"name": "one", "some_int": 1}, {"name": "two", "some_int": 2}, {"name": "three", "some_int": 3}, {"name": "four", "some_int": 4}]
}
UNIQUE_B_AND_A_INDEXED_LISTS = {
    "some_indexed_list": [{"name": "three", "some_int": 3}, {"name": "four", "some_int": 4}, {"name": "one", "some_int": 1}, {"name": "two", "some_int": 2}]
}


@pytest.mark.parametrize(
    ("a_data", "b_data", "list_merge", "expected"),
    [
        pytest.param({}, {}, "append_unique", {}, id="empty_data"),
        # Testing AvdList
        pytest.param(A_LIST, B_LIST, "append_unique", UNIQUE_A_AND_B_LISTS, id="list_append_unique"),
        pytest.param(A_LIST, B_LIST, "append", ALL_A_AND_B_LISTS, id="list_append"),
        pytest.param(A_LIST, B_LIST, "replace", B_LIST, id="list_replace"),
        pytest.param(A_LIST, B_LIST, "keep", A_LIST, id="list_keep"),
        pytest.param(A_LIST, B_LIST, "prepend", ALL_B_AND_A_LISTS, id="list_prepend"),
        pytest.param(A_LIST, B_LIST, "prepend_unique", UNIQUE_B_AND_A_LISTS, id="list_prepend_unique"),
        # Testing AvdIndexedList
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "append_unique", UNIQUE_A_AND_B_INDEXED_LISTS, id="indexed_list_append_unique"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "append", UNIQUE_A_AND_B_INDEXED_LISTS, id="indexed_list_append"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "replace", B_INDEXED_LIST, id="indexed_list_replace"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "keep", A_INDEXED_LIST, id="indexed_list_keep"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "prepend", UNIQUE_B_AND_A_INDEXED_LISTS, id="indexed_list_prepend"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "prepend_unique", UNIQUE_B_AND_A_INDEXED_LISTS, id="indexed_list_prepend_unique"),
    ],
)
def test_data_merging(
    a_data: dict,
    b_data: dict,
    list_merge: Literal["append_unique", "append", "replace", "keep", "prepend", "prepend_unique"],
    expected: dict,
    data_merging_schema_class: DataMergingTestSchema,
) -> None:
    a = data_merging_schema_class._from_dict(a_data)
    b = data_merging_schema_class._from_dict(b_data)
    assert a._deepmerged(b, list_merge=list_merge)._as_dict() == expected


A_MODEL = {"some_object": {"name": "one", "some_int": 1}}
B_MODEL = {"some_object": {"some_int": 2, "some_str": "blah"}}
C_MODEL = {"some_object": {"some_int": 1}}
MERGED_MODEL_SOURCE_A_B = {
    "some_object": "a.some_object",
    "some_object.name": "a.some_object.name",
    "some_object.some_int": "b.some_object.some_int",
    "some_object.some_str": "b.some_object.some_str",
}
MERGED_MODEL_SOURCE_A_C = {
    "some_object": "a.some_object",
    "some_object.name": "a.some_object.name",
    "some_object.some_int": "a.some_object.some_int",
}


@pytest.mark.parametrize(
    ("a_data", "b_data", "list_merge", "expected_sources"),
    [
        # Testing AvdModel
        pytest.param(A_MODEL, B_MODEL, "append_unique", MERGED_MODEL_SOURCE_A_B, id="merging AvdModel"),
        pytest.param(A_MODEL, C_MODEL, "append_unique", MERGED_MODEL_SOURCE_A_C, id="merging AvdModel"),
    ],
)
def test_data_merging_source_model(
    a_data: dict,
    b_data: dict,
    list_merge: Literal["append_unique", "append", "replace", "keep", "prepend", "prepend_unique"],
    expected_sources: list,
    data_merging_schema_class: DataMergingTestSchema,
) -> None:
    a = data_merging_schema_class._from_dict(a_data, data_source=InputPath("a"))
    b = data_merging_schema_class._from_dict(b_data, data_source=InputPath("b"))
    merged = a._deepmerged(b, list_merge=list_merge)
    for object_path, expected_source in expected_sources.items():
        split = object_path.split(".")
        # init
        parent = None
        current = merged
        for attr in split:
            parent = current
            current = current._get_defined_attr(attr)
        print(current)
        if isinstance(current, AvdBase):
            assert str(current._source) == expected_source
        else:  # field
            assert parent._get_field_source(split[-1]) == expected_source


MERGED_LIST_APPEND_UNIQUE = ["a.some_list[0]", "a.some_list[1]", "b.some_list[1]", "b.some_list[2]"]
MERGED_LIST_APPEND = ["a.some_list[0]", "a.some_list[1]", "b.some_list[0]", "b.some_list[1]", "b.some_list[2]"]
MERGED_LIST_KEEP = ["a.some_list[0]", "a.some_list[1]"]
MERGED_LIST_REPLACE = ["b.some_list[0]", "b.some_list[1]", "b.some_list[2]"]
MERGED_LIST_PREPEND = ["b.some_list[0]", "b.some_list[1]", "b.some_list[2]", "a.some_list[0]", "a.some_list[1]"]
MERGED_LIST_PREPEND_UNIQUE = ["b.some_list[1]", "b.some_list[2]", "a.some_list[0]", "a.some_list[1]"]


@pytest.mark.parametrize(
    ("a_data", "b_data", "list_merge", "expected_sources"),
    [
        # Testing AvdList
        pytest.param(A_LIST, B_LIST, "append_unique", MERGED_LIST_APPEND_UNIQUE, id="list_append_unique"),
        pytest.param(A_LIST, B_LIST, "append", MERGED_LIST_APPEND, id="list_append"),
        pytest.param(A_LIST, B_LIST, "replace", MERGED_LIST_REPLACE, id="list_replace"),
        pytest.param(A_LIST, B_LIST, "keep", MERGED_LIST_KEEP, id="list_keep"),
        pytest.param(A_LIST, B_LIST, "prepend_unique", MERGED_LIST_PREPEND_UNIQUE, id="list_prepend_unique"),
        pytest.param(A_LIST, B_LIST, "prepend", MERGED_LIST_PREPEND, id="list_prepend"),
    ],
)
def test_data_merging_source_list(
    a_data: dict,
    b_data: dict,
    list_merge: Literal["append_unique", "append", "replace", "keep", "prepend", "prepend_unique"],
    expected_sources: list,
    data_merging_schema_class: DataMergingTestSchema,
) -> None:
    a = data_merging_schema_class._from_dict(a_data, data_source=InputPath("a"))
    b = data_merging_schema_class._from_dict(b_data, data_source=InputPath("b"))
    merged = a._deepmerged(b, list_merge=list_merge)
    for index, expected_source in enumerate(expected_sources):
        assert str(merged.some_list._items_source[index]) == expected_source


MERGED_INDEXED_LIST_APPEND = [
    "a.some_indexed_list[name=one]",
    "a.some_indexed_list[name=two]",
    "b.some_indexed_list[name=three]",
    "b.some_indexed_list[name=four]",
]
MERGED_INDEXED_LIST_KEEP = ["a.some_indexed_list[name=one]", "a.some_indexed_list[name=two]"]
MERGED_INDEXED_LIST_REPLACE = ["b.some_indexed_list[name=two]", "b.some_indexed_list[name=three]", "b.some_indexed_list[name=four]"]
MERGED_INDEXED_LIST_PREPEND = [
    "b.some_indexed_list[name=three]",
    "b.some_indexed_list[name=four]",
    "a.some_indexed_list[name=one]",
    "a.some_indexed_list[name=two]",
]


@pytest.mark.parametrize(
    ("a_data", "b_data", "list_merge", "expected_sources"),
    [
        # Testing AvdList
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "append", MERGED_INDEXED_LIST_APPEND, id="list_append"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "replace", MERGED_INDEXED_LIST_REPLACE, id="list_replace"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "keep", MERGED_INDEXED_LIST_KEEP, id="list_keep"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "prepend", MERGED_INDEXED_LIST_PREPEND, id="list_prepend"),
    ],
)
def test_data_merging_source_indexed_list(
    a_data: dict,
    b_data: dict,
    list_merge: Literal["append_unique", "append", "replace", "keep", "prepend", "prepend_unique"],
    expected_sources: list,
    data_merging_schema_class: DataMergingTestSchema,
) -> None:
    a = data_merging_schema_class._from_dict(a_data, data_source=InputPath("a"))
    b = data_merging_schema_class._from_dict(b_data, data_source=InputPath("b"))
    merged = a._deepmerged(b, list_merge=list_merge)
    for item, expected_source in zip(merged.some_indexed_list.values(), expected_sources, strict=False):
        assert str(item._source) == expected_source


@pytest.mark.parametrize(
    ("a_data", "b_data", "list_merge", "expected"),
    [
        pytest.param({}, {}, "append_unique", {}, id="empty_data"),
        # Testing AvdList
        pytest.param(A_LIST, B_LIST, "append_unique", UNIQUE_A_AND_B_LISTS, id="list_append_unique"),
        pytest.param(A_LIST, B_LIST, "append", ALL_A_AND_B_LISTS, id="list_append"),
        pytest.param(A_LIST, B_LIST, "replace", B_LIST, id="list_replace"),
        pytest.param(A_LIST, B_LIST, "keep", A_LIST, id="list_keep"),
        pytest.param(A_LIST, B_LIST, "prepend", ALL_B_AND_A_LISTS, id="list_prepend"),
        pytest.param(A_LIST, B_LIST, "prepend_unique", UNIQUE_B_AND_A_LISTS, id="list_prepend_unique"),
        # Testing AvdIndexedList
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "append_unique", UNIQUE_A_AND_B_INDEXED_LISTS, id="indexed_list_append_unique"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "append", UNIQUE_A_AND_B_INDEXED_LISTS, id="indexed_list_append"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "replace", B_INDEXED_LIST, id="indexed_list_replace"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "keep", A_INDEXED_LIST, id="indexed_list_keep"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "prepend", UNIQUE_B_AND_A_INDEXED_LISTS, id="indexed_list_prepend"),
        pytest.param(A_INDEXED_LIST, B_INDEXED_LIST, "prepend_unique", UNIQUE_B_AND_A_INDEXED_LISTS, id="indexed_list_prepend_unique"),
    ],
)
def test_data_merging_source(
    a_data: dict,
    b_data: dict,
    list_merge: Literal["append_unique", "append", "replace", "keep", "prepend", "prepend_unique"],
    expected: dict,
    data_merging_schema_class: DataMergingTestSchema,
) -> None:
    a = data_merging_schema_class._from_dict(a_data)
    b = data_merging_schema_class._from_dict(b_data)
    merged = a._deepmerged(b, list_merge=list_merge)
    validate_merged_path(merged, a, b, list_merge)


def validate_merged_path(merged_object: AvdBase, a: AvdBase, b: AvdBase, list_merge: str) -> None:
    """TODO"""
    # TODO : if a and b are Undefined -great sadness
    # The object was created from deepmerging b into a.
    assert str(merged_object._source) == (str(a._source) if a is not Undefined else str(b._source))
    if isinstance(merged_object, AvdModel):
        print(f"merged {merged_object._as_dict()} of type {type(merged_object)}")
        a = cast(AvdModel, a)
        b = cast(AvdModel, b)
        for key, value in merged_object.items():
            if isinstance(value, AvdBase):
                validate_merged_path(value, a._get(key), b._get(key), list_merge)
            assert merged_object._get_field_source(key) == a._get_field_source(key) if hasattr(a, key) else b._get_field_source(key)
    elif isinstance(merged_object, AvdList):
        # This logic is strategy dependent
        print(f"merged {merged_object._as_list()} of type {type(merged_object)}")
        a = cast(AvdList, a)
        b = cast(AvdList, b)
        print(merged_object._items_source, a._items_source, b._items_source)
        for index, item in enumerate(merged_object):
            # TODO: check if this works for multiple repeated values for unique
            try:
                a_index = a._items.index(item)
            except ValueError:
                a_index = None
            try:
                b_index = b._items.index(item)
            except ValueError:
                b_index = None
            print(f"{a}, {a_index}, {b}, {b_index} - {item}")
            if list_merge == "append_unique":
                if a_index is not None:
                    src = a
                    src_index = a_index
                else:
                    src = b
                    src_index = b_index
            elif list_merge == "append":
                src = a if index < len(a) else b
                src_index = index if index < len(a) else index - len(a)
            elif list_merge == "keep":
                src = a
                src_index = index
            elif list_merge == "replace":
                src = b
                src_index = index
            elif list_merge == "prepend":
                src = b if index < len(b) else a
                src_index = index if index < len(b) else index - len(b)
            elif list_merge == "prepend_unique":
                if a_index is not None:
                    src = a
                    src_index = a_index
                else:
                    src = b
                    src_index = b_index

            print(f"List item {item} in {src} - {src_index}")
            assert str(merged_object._items_source[index]) == str(src._items_source[src_index])
            # if isinstance(item, AvdBase):
            # TODO: Fix this
            # validate_merged_path(item, a, b, list_merge)

    elif isinstance(merged_object, AvdIndexedList):
        print(f"merged {merged_object._as_list()} of type {type(merged_object)}")
        # This logic is strategy dependent
        a = cast(AvdIndexedList[str, merged_object._item_type], a)
        b = cast(AvdIndexedList[str, merged_object._item_type], b)
        for item in merged_object:
            primary_key = item._get(merged_object._primary_key)
            print(primary_key)
            if primary_key in a:
                a_item = a.obtain(primary_key)
            else:
                a_item = Undefined
            if primary_key in b:
                b_item = b.obtain(primary_key)
            else:
                b_item = Undefined
            assert str(item._source) == str(a_item._source if primary_key in a else b_item._source)

            validate_merged_path(item, a_item, b_item, list_merge)
