import typing as t
from typing import ClassVar

import pytest

from sim_server.core.namelist import (
    Bool,
    Float,
    Int,
    ListInt,
    ListStr,
    Namelist,
    Str,
)


class Simple(Namelist):
    x: Int
    y: Float
    name: Str
    flag: Bool


def test_scalar_fields_output():
    nml = Simple(x=1, y=2.5, name="foo", flag=True)
    assert nml.to_nml() == "x = 1\ny = 2.5\nname = 'foo'\nflag = T"


def test_bool_false():
    class N(Namelist):
        b: Bool

    assert N(b=False).to_nml() == "b = F"


def test_list_int():
    class N(Namelist):
        vals: ListInt

    assert N(vals=[1, 2, 3]).to_nml() == "vals = 1, 2, 3"


def test_list_str():
    class N(Namelist):
        names: ListStr

    assert N(names=["a", "b"]).to_nml() == "names = 'a', 'b'"


def test_rejects_plain_type():
    with pytest.raises(TypeError, match="missing NamelistField"):

        class Bad(Namelist):
            x: int


def test_rejects_annotated_without_namelist_field():
    with pytest.raises(TypeError, match="missing NamelistField"):

        class Bad(Namelist):
            x: t.Annotated[int, "not a NamelistField"]


def test_valid_fields_accepted():
    class Good(Namelist):
        x: Int
        y: Str

    assert Good(x=1, y="hi").to_nml() == "x = 1\ny = 'hi'"


def test_strict_false():
    class Bad(Namelist):
        strict_nml: ClassVar[bool] = False
        x: int
        y: Str

    assert Bad(x=1, y="hi").to_nml() == "y = 'hi'"
