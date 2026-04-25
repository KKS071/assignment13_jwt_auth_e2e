# File: tests/integration/test_calculation.py
# Purpose: Unit tests for calculation model get_result() methods

import pytest
from app.models.calculation import Addition, Subtraction, Multiplication, Division, Calculation


def _calc(klass, inputs):
    c = klass()
    c.inputs = inputs
    return c


# ── Addition ───────────────────────────────────────────────────────────────

def test_addition_basic():
    assert _calc(Addition, [1, 2, 3]).get_result() == 6


def test_addition_two_numbers():
    assert _calc(Addition, [5, 5]).get_result() == 10


def test_addition_single_input_raises():
    with pytest.raises(ValueError, match="at least two"):
        _calc(Addition, [5]).get_result()


def test_addition_bad_inputs_raises():
    with pytest.raises(ValueError, match="list"):
        _calc(Addition, "not a list").get_result()


# ── Subtraction ────────────────────────────────────────────────────────────

def test_subtraction_basic():
    assert _calc(Subtraction, [10, 3, 2]).get_result() == 5


def test_subtraction_single_raises():
    with pytest.raises(ValueError, match="at least two"):
        _calc(Subtraction, [10]).get_result()


def test_subtraction_bad_inputs():
    with pytest.raises(ValueError, match="list"):
        _calc(Subtraction, 99).get_result()


# ── Multiplication ─────────────────────────────────────────────────────────

def test_multiplication_basic():
    assert _calc(Multiplication, [2, 3, 4]).get_result() == 24


def test_multiplication_with_zero():
    assert _calc(Multiplication, [5, 0, 3]).get_result() == 0


def test_multiplication_single_raises():
    with pytest.raises(ValueError, match="at least two"):
        _calc(Multiplication, [7]).get_result()


def test_multiplication_bad_inputs():
    with pytest.raises(ValueError, match="list"):
        _calc(Multiplication, 42).get_result()


# ── Division ───────────────────────────────────────────────────────────────

def test_division_basic():
    assert _calc(Division, [100, 5, 2]).get_result() == 10.0


def test_division_by_zero():
    with pytest.raises(ValueError, match="divide by zero"):
        _calc(Division, [10, 0]).get_result()


def test_division_single_raises():
    with pytest.raises(ValueError, match="at least two"):
        _calc(Division, [10]).get_result()


def test_division_bad_inputs():
    with pytest.raises(ValueError, match="list"):
        _calc(Division, "bad").get_result()


# ── Factory ────────────────────────────────────────────────────────────────

def test_factory_addition():
    import uuid
    calc = Calculation.create("addition", uuid.uuid4(), [1, 2])
    assert isinstance(calc, Addition)


def test_factory_subtraction():
    import uuid
    calc = Calculation.create("subtraction", uuid.uuid4(), [5, 3])
    assert isinstance(calc, Subtraction)


def test_factory_multiplication():
    import uuid
    calc = Calculation.create("multiplication", uuid.uuid4(), [2, 3])
    assert isinstance(calc, Multiplication)


def test_factory_division():
    import uuid
    calc = Calculation.create("division", uuid.uuid4(), [10, 2])
    assert isinstance(calc, Division)


def test_factory_invalid_type():
    import uuid
    with pytest.raises(ValueError, match="Unsupported"):
        Calculation.create("modulo", uuid.uuid4(), [10, 3])


# ── Schema validation ──────────────────────────────────────────────────────

def test_schema_valid_addition():
    from app.schemas.calculation import CalculationBase
    c = CalculationBase(type="addition", inputs=[1, 2, 3])
    assert c.type == "addition"


def test_schema_division_by_zero():
    from app.schemas.calculation import CalculationBase
    with pytest.raises(Exception, match="divide by zero"):
        CalculationBase(type="division", inputs=[10, 0])


def test_schema_too_few_inputs():
    from app.schemas.calculation import CalculationBase
    with pytest.raises(Exception):
        CalculationBase(type="addition", inputs=[1])


def test_schema_non_list_inputs():
    from app.schemas.calculation import CalculationBase
    with pytest.raises(Exception):
        CalculationBase(type="addition", inputs="notalist")


def test_schema_invalid_type():
    from app.schemas.calculation import CalculationBase
    with pytest.raises(Exception):
        CalculationBase(type="modulo", inputs=[1, 2])


def test_schema_repr():
    import uuid
    calc = Calculation.create("addition", uuid.uuid4(), [1, 2])
    assert "addition" in repr(calc)
