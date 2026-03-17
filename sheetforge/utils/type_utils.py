from __future__ import annotations

from dataclasses import dataclass


BASE_TYPES = {"int", "long", "float", "double", "bool", "string"}


@dataclass(frozen=True)
class TypeDescriptor:
    raw: str
    key_type: str | None = None
    value_type: str | None = None
    element_type: str | None = None


class TypeParser:
    @staticmethod
    def parse(type_str: str) -> TypeDescriptor:
        value = type_str.strip()
        if value.endswith("[][]"):
            return TypeDescriptor(raw=value, element_type=value[:-4].strip())
        if value.endswith("[]"):
            return TypeDescriptor(raw=value, element_type=value[:-2].strip())
        if value.startswith("set<") and value.endswith(">"):
            return TypeDescriptor(raw=value, element_type=value[4:-1].strip())
        if "->" in value:
            key_type, value_type = [part.strip() for part in value.split("->", 1)]
            return TypeDescriptor(raw=value, key_type=key_type, value_type=value_type)
        return TypeDescriptor(raw=value, element_type=value)


class TypeInferrer:
    @classmethod
    def infer_column(cls, values: list[str]) -> str:
        non_empty = [value.strip() for value in values if value.strip()]
        if not non_empty:
            return "string"

        inferred = [cls.infer_value(value) for value in non_empty]
        if all(value == inferred[0] for value in inferred):
            return inferred[0]

        unique = set(inferred)
        if unique <= {"int", "long"}:
            return "long"
        if unique <= {"int", "long", "float", "double"}:
            return "float"
        return "string"

    @classmethod
    def infer_value(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return "string"
        if value.lower() in {"true", "false", "yes", "no"}:
            return "bool"
        if ":" in value and "," in value:
            return cls._infer_map_type(value)
        if ";" in value:
            return cls._infer_array2d_type(value)
        if "," in value:
            return cls._infer_array_type(value)
        if value.endswith(("L", "l")):
            try:
                int(value[:-1])
                return "long"
            except ValueError:
                pass
        if "." in value:
            try:
                float(value)
                return "float"
            except ValueError:
                pass
        try:
            int(value)
            return "int"
        except ValueError:
            return "string"

    @classmethod
    def _infer_array_type(cls, value: str) -> str:
        element_type = cls._merge_scalar_types([cls.infer_scalar(part.strip()) for part in value.split(",") if part.strip()])
        return f"{element_type}[]"

    @classmethod
    def _infer_array2d_type(cls, value: str) -> str:
        parts: list[str] = []
        for row in value.split(";"):
            parts.extend(part.strip() for part in row.split(",") if part.strip())
        element_type = cls._merge_scalar_types([cls.infer_scalar(part) for part in parts])
        return f"{element_type}[][]"

    @classmethod
    def _infer_map_type(cls, value: str) -> str:
        key_types: list[str] = []
        value_types: list[str] = []
        for pair in value.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            key, item = [part.strip() for part in pair.split(":", 1)]
            key_types.append(cls.infer_scalar(key))
            value_types.append(cls.infer_scalar(item))
        return f"{cls._merge_scalar_types(key_types)}->{cls._merge_scalar_types(value_types)}"

    @classmethod
    def infer_scalar(cls, value: str) -> str:
        scalar = cls.infer_value(value)
        if any(token in scalar for token in ("[]", "->")):
            return "string"
        return scalar

    @staticmethod
    def _merge_scalar_types(types: list[str]) -> str:
        unique = set(types) if types else {"string"}
        if unique <= {"bool"}:
            return "bool"
        if unique <= {"int"}:
            return "int"
        if unique <= {"int", "long"}:
            return "long"
        if unique <= {"int", "long", "float", "double"}:
            return "float"
        if unique <= {"string"}:
            return "string"
        return "string"


__all__ = ["BASE_TYPES", "TypeDescriptor", "TypeInferrer", "TypeParser"]
