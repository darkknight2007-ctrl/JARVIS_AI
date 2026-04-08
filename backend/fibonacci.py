def fibonacci(n):
    """
    Calculate the nth Fibonacci number using iterative approach.
    
    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)
    
    Returns:
        int: The nth Fibonacci number
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b

def fibonacci_sequence(count):
    """
    Generate the first 'count' numbers in the Fibonacci sequence.
    
    Args:
        count (int): Number of Fibonacci numbers to generate
    
    Returns:
        list: List of Fibonacci numbers
    """
    if count <= 0:
        return []
    elif count == 1:
        return [0]
    elif count == 2:
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, count):
        sequence.append(sequence[i-1] + sequence[i-2])
    
    return sequence

if __name__ == "__main__":
    # Example usage
    print("First 10 Fibonacci numbers:")
    print(fibonacci_sequence(10))
    
    print("\nIndividual Fibonacci numbers:")
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")