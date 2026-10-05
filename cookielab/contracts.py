"""Strict bounded input admission, adapted from Jake's MIT redirect/range labs.

Native types are checked by identity before any caller-controlled operation.
"""

import json
import re

INPUT_BYTES = 65_536
OUTPUT_BYTES = 524_288
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", re.ASCII)
FEATURE = re.compile(r"[a-z][a-z0-9-]{0,31}", re.ASCII)


class Invalid(ValueError):
    """An invalid document or failed delivery, with a fixed diagnostic code."""


def text(value, limit=256):
    if type(value) is not str or len(value) > limit:
        raise Invalid("TEXT_TYPE_OR_LIMIT")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise Invalid("TEXT_CONTROL")
    try:
        value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise Invalid("INVALID_UNICODE") from exc


def _walk(value, depth, budget, active):
    kind = type(value)
    # Equality against a tuple/set of types can itself invoke exotic metaclasses.
    if not (kind is dict or kind is list or kind is str or kind is int
            or kind is bool or value is None):
        raise Invalid("TREE_TYPE")
    budget[0] += 1
    if budget[0] > 5_000:
        raise Invalid("NODE_LIMIT")
    if (kind is dict or kind is list) and depth > 8:
        raise Invalid("TREE_DEPTH")
    if kind is str:
        text(value)
    elif kind is int:
        if value < -9_999_999_999 or value > 9_999_999_999:
            raise Invalid("INTEGER_TOKEN_BOUND")
    elif kind is dict or kind is list:
        if id(value) in active:
            raise Invalid("TREE_CYCLE")
        if len(value) > 100:
            raise Invalid("CONTAINER_LIMIT")
        active.add(id(value))
        try:
            if kind is dict:
                for key, item in value.items():
                    if type(key) is not str:
                        raise Invalid("TREE_TYPE")
                    budget[0] += 1
                    if budget[0] > 5_000:
                        raise Invalid("NODE_LIMIT")
                    text(key, 64)
                    _walk(item, depth + 1, budget, active)
            else:
                for item in value:
                    _walk(item, depth + 1, budget, active)
        finally:
            active.remove(id(value))


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid("DUPLICATE_KEY")
        result[key] = value
    return result


def _integer(source):
    if len(source.lstrip("-")) > 10:
        raise Invalid("INTEGER_TOKEN_BOUND")
    return int(source)


def _noninteger(_source):
    raise Invalid("NONINTEGER_JSON")


def parse(raw):
    """Parse bounded UTF8 JSON bytes; evaluate performs full native/schema admission."""
    if type(raw) is not bytes or len(raw) > INPUT_BYTES:
        raise Invalid("INPUT_LIMIT")
    try:
        source = raw.decode("utf-8", "strict")
        quoted = escaped = False
        depth = 0
        for char in source:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > 8:
                    raise Invalid("JSON_DEPTH")
            elif char in "]}":
                depth -= 1
        return json.loads(source, object_pairs_hook=_pairs, parse_int=_integer,
                          parse_float=_noninteger, parse_constant=_noninteger)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if type(exc) is Invalid:
            raise
        raise Invalid("INVALID_JSON") from exc


def _keys(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise Invalid("SCHEMA")


def _list(value, lower, upper, code):
    if type(value) is not list or not lower <= len(value) <= upper:
        raise Invalid(code)


def _choice(value, choices, code):
    if type(value) is not str or value not in choices:
        raise Invalid(code)


def _nullable_text(value):
    if value is not None and type(value) is not str:
        raise Invalid("NULL_TEXT_TYPE")


def _bool(value):
    if value is not None and type(value) is not bool:
        raise Invalid("BOOL_TYPE")


def _time(value):
    if value is not None and (type(value) is not int or not 0 <= value <= 9_999_999_999):
        raise Invalid("TIME")


def validate(document):
    """Admit the WHOLE exact-native document before any scope decision."""
    _walk(document, 1, [0], set())
    if len(json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > INPUT_BYTES:
        raise Invalid("INPUT_LIMIT")
    _keys(document, ("version", "cases"))
    if type(document["version"]) is not int or document["version"] != 1:
        raise Invalid("VERSION")
    _list(document["cases"], 1, 40, "CASE_COUNT")
    seen = set()
    for case in document["cases"]:
        _keys(case, ("id", "cookie", "request", "unsupported_features"))
        text(case["id"], 64)
        if not IDENTIFIER.fullmatch(case["id"]):
            raise Invalid("ID_FORMAT")
        if case["id"] in seen:
            raise Invalid("DUPLICATE_CASE_ID")
        seen.add(case["id"])
        cookie, request = case["cookie"], case["request"]
        _keys(cookie, ("domain", "host_only", "path", "secure", "lifetime", "expires_at"))
        _keys(request, ("host", "path", "secure_transport", "now"))
        for value in (cookie["domain"], cookie["path"], request["host"], request["path"]):
            _nullable_text(value)
        for value in (cookie["host_only"], cookie["secure"], request["secure_transport"]):
            _bool(value)
        _choice(cookie["lifetime"], ("session", "persistent", "unknown"), "LIFETIME")
        _time(cookie["expires_at"])
        _time(request["now"])
        if cookie["lifetime"] != "persistent" and cookie["expires_at"] is not None:
            raise Invalid("EXPIRY_SHAPE")
        features = case["unsupported_features"]
        _list(features, 0, 8, "FEATURE_LIST")
        used = set()
        for feature in features:
            if type(feature) is not str or not FEATURE.fullmatch(feature):
                raise Invalid("FEATURE_FORMAT")
            if feature in used:
                raise Invalid("FEATURE_DUPLICATE")
            used.add(feature)

