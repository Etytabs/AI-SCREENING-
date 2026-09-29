def binary_accuracy(predictions: list[bool], labels: list[bool]) -> float:
    if len(predictions) != len(labels) or not labels:
        raise ValueError("Predictions and labels must have the same non-zero length.")
    return sum(p == y for p, y in zip(predictions, labels)) / len(labels)

def mean_absolute_error(predictions: list[float], labels: list[float]) -> float:
    if len(predictions) != len(labels) or not labels:
        raise ValueError("Predictions and labels must have the same non-zero length.")
    return sum(abs(p - y) for p, y in zip(predictions, labels)) / len(labels)
