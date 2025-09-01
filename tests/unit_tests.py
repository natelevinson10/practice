import pytest

def add(a, b):
    """Return the sum of a and b."""
    return a + b


def is_even(n):
    """Return True if n is even, False otherwise."""
    return n % 2 == 0


def divide(a, b):
    """Return a divided by b. Raises ZeroDivisionError if b == 0."""
    return a / b




def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_is_even():
    assert is_even(2) is True
    assert is_even(3) is False


def test_divide():
    assert divide(10, 2) == 5
    assert divide(9, 3) == 3

    # check that dividing by zero raises the right exception
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)

def test_fail_add_test():
    assert add(2, 3) == 4

