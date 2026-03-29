from typing import ClassVar

import pytest  #

from sim_server.core.namelist import Int, Namelist, NamelistFile, Str


class Section(Namelist):
    x: Int


class TwoFields(Namelist):
    x: Int
    y: Str


def test_single_section():
    class F(NamelistFile):
        section: Section

    result = F(section=Section(x=1)).to_nml()
    assert result == "&section\nx = 1\n/"


def test_multiple_sections():
    class F(NamelistFile):
        a: Section
        b: Section

    result = F(a=Section(x=1), b=Section(x=2)).to_nml()
    assert result == "&a\nx = 1\n/\n&b\nx = 2\n/"


def test_list_of_sections():
    class F(NamelistFile):
        section: list[Section]

    result = F(section=[Section(x=1), Section(x=2)]).to_nml()
    assert result == "&section\nx = 1\n/\n&section\nx = 2\n/"


def test_section_content():
    class F(NamelistFile):
        nml: TwoFields

    result = F(nml=TwoFields(x=42, y="hello")).to_nml()
    assert result == "&nml\nx = 42\ny = 'hello'\n/"


def test_section_content_strict_false():
    class F(NamelistFile):
        strict_nml: ClassVar[bool] = False
        nml: TwoFields
        i: int = 4

    result = F(nml=TwoFields(x=42, y="hello")).to_nml()
    assert result == "&nml\nx = 42\ny = 'hello'\n/"


def test_bad():
    with pytest.raises(
        TypeError,
        match="F.i must be a subclass of Namelist or a list of subclass of Namelist",
    ):

        class F(NamelistFile):
            nml: TwoFields
            i: int = 4
