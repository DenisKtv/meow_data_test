import psutil


def measure_memory():
    """Возвращае использование памяти в мегабайтах"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def profile_memory_usage(func, *args, **kwargs):
    """Проверяет использование памяти переданной функции"""
    initial_memory = measure_memory()
    result = func(*args, **kwargs)
    final_memory = measure_memory()
    print(
        f'Memory used by {func.__name__}: {final_memory - initial_memory} MB'
    )
    return result
