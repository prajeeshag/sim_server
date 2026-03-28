import typing as t
from typing import ClassVar

from pydantic import BaseModel


def str2txt(v: str) -> str:
    return f"'{v}'"


def num2txt(v: int | float) -> str:
    return str(v)


def bool2txt(v: bool) -> str:
    return "T" if v else "F"


def str2nml(v: str) -> str:
    return f" = {str2txt(v)}"


def num2nml(v: int | float) -> str:
    return f" = {num2txt(v)}"


def bool2nml(v: bool) -> str:
    return f" = {bool2txt(v)}"


def list2txt(
    v: list,
    to_nml: t.Callable[[t.Any], str],
    line_length: int = 80,
    indent: str = "    ",
) -> str:
    items = [to_nml(x) for x in v]
    lines = []
    current = ""
    for i, item in enumerate(items):
        candidate = (current + ", " + item) if current else item
        if current and len(candidate) > line_length:
            lines.append(current + ",")
            current = indent + item
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def _get_to_nml(
    v: list,
) -> t.Callable[[t.Any], str]:
    elem_type = type(v[0])
    if elem_type is str:
        to_nml = str2txt
    elif elem_type is int or elem_type is float:
        to_nml = num2txt
    elif elem_type is bool:
        to_nml = bool2txt
    else:
        raise ValueError(f"Unsupported type {type}")
    return to_nml


def list2nml(v: list) -> str:
    to_nml = _get_to_nml(v)
    return f" = {list2txt(v, to_nml)}"


class NamelistField:
    def __init__(self, to_nml: t.Callable[[t.Any], str]):
        self.to_nml = to_nml


Str = t.Annotated[str, NamelistField(to_nml=str2nml)]
Int = t.Annotated[int, NamelistField(to_nml=num2nml)]
Float = t.Annotated[float, NamelistField(to_nml=num2nml)]
Bool = t.Annotated[bool, NamelistField(to_nml=bool2nml)]
ListStr = t.Annotated[list[str], NamelistField(to_nml=list2nml)]
ListInt = t.Annotated[list[int], NamelistField(to_nml=list2nml)]
ListFloat = t.Annotated[list[float], NamelistField(to_nml=list2nml)]
ListBool = t.Annotated[list[bool], NamelistField(to_nml=list2nml)]


def get_namelist_field(meta):
    for m in meta:
        if isinstance(m, NamelistField):
            return m
    return None


def get_base_type(field):
    if t.get_origin(field) is t.Annotated:
        base, *_ = t.get_args(field)
        return base
    return field


class Namelist(BaseModel):
    strict_nml: ClassVar[bool] = True

    def to_nml(self) -> str:
        lines: list[str] = []
        for name, field in self.model_fields.items():
            value = getattr(self, name)
            nl_field = get_namelist_field(field.metadata)
            if nl_field is None:
                if self.strict_nml:
                    raise ValueError(f"No NamelistField for {name}")
                continue
            lines.append(f"{name}{nl_field.to_nml(value)}")
        return "\n".join(lines)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)
        if not cls.strict_nml:
            return
        for name, field in cls.model_fields.items():
            if not any(isinstance(m, NamelistField) for m in field.metadata):
                raise TypeError(f"{cls.__name__}.{name} missing NamelistField")


class NamelistFile(BaseModel):
    strict_nml: ClassVar[bool] = True

    def to_nml(self) -> str:
        lines: list[str] = []
        for name, field in self.model_fields.items():
            value = getattr(self, name)
            if isinstance(value, Namelist):
                lines.append(f"&{name}")
                lines.append(value.to_nml())
                lines.append("/")
                continue
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, Namelist):
                        lines.append(f"&{name}")
                        lines.append(item.to_nml())
                        lines.append("/")
                        continue
                    else:
                        if self.strict_nml:
                            raise ValueError(
                                f"Unsupported type for {name}: {type(item)}"
                            )
            else:
                if self.strict_nml:
                    raise ValueError(f"Unsupported type for {name}: {type(value)}")
                    lines.append(f"{name} = {value}")
        return "\n".join(lines)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.strict_nml:
            return
        for name, field in cls.model_fields.items():
            typ = field.annotation
            if t.get_origin(typ) is list:
                inner = get_base_type(typ.__args__[0])
                if not issubclass(inner, Namelist):
                    raise TypeError(
                        f"{cls.__name__}.{name}"
                        + " must be a subclass of Namelist"
                        + " or a list of subclass of Namelist"
                    )

            else:
                if not issubclass(typ, Namelist):
                    raise TypeError(
                        f"{cls.__name__}.{name}"
                        + " must be a subclass of Namelist"
                        + " or a list of subclass of Namelist"
                    )
