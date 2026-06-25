from pydantic_ai import FunctionToolset


def average(numbers: list[float | int]) -> float:
    """Compute the average of a list of numbers.

    Args:
        numbers: List of numbers to average.

    Returns:
        The average of the numbers.
    """
    if not numbers:
        raise ValueError("Cannot compute average of an empty list.")
    return sum(numbers) / len(numbers)


def median(numbers: list[float | int]) -> float:
    """Compute the median of a list of numbers.

    Args:
        numbers: List of numbers to compute the median.

    Returns:
        The median of the numbers.
    """
    if not numbers:
        raise ValueError("Cannot compute median of an empty list.")
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_numbers[mid - 1] + sorted_numbers[mid]) / 2
    else:
        return sorted_numbers[mid]


statistic_toolset = FunctionToolset(tools=[average, median])
