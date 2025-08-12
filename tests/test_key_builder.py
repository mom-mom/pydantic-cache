from pydantic_cache.key_builder import default_key_builder


class TestKeyBuilder:
    def test_basic_key_generation(self):
        def sample_func():
            pass

        key = default_key_builder(sample_func, namespace="test", args=(1, 2, 3), kwargs={"a": 1, "b": 2})

        assert key.startswith("test:")
        assert len(key) > len("test:")

    def test_same_args_same_key(self):
        def sample_func():
            pass

        key1 = default_key_builder(sample_func, namespace="test", args=(1, "hello", True), kwargs={"x": 10})

        key2 = default_key_builder(sample_func, namespace="test", args=(1, "hello", True), kwargs={"x": 10})

        assert key1 == key2

    def test_different_args_different_keys(self):
        def sample_func():
            pass

        key1 = default_key_builder(sample_func, namespace="test", args=(1, 2), kwargs={})

        key2 = default_key_builder(
            sample_func,
            namespace="test",
            args=(2, 1),  # Different order
            kwargs={},
        )

        assert key1 != key2

    def test_different_kwargs_different_keys(self):
        def sample_func():
            pass

        key1 = default_key_builder(sample_func, namespace="test", args=(), kwargs={"a": 1, "b": 2})

        key2 = default_key_builder(
            sample_func,
            namespace="test",
            args=(),
            kwargs={"a": 1, "b": 3},  # Different value
        )

        assert key1 != key2

    def test_different_functions_different_keys(self):
        def func1():
            pass

        def func2():
            pass

        key1 = default_key_builder(func1, namespace="test", args=(1,), kwargs={})

        key2 = default_key_builder(func2, namespace="test", args=(1,), kwargs={})

        assert key1 != key2

    def test_namespace_isolation(self):
        def sample_func():
            pass

        key1 = default_key_builder(sample_func, namespace="namespace1", args=(1,), kwargs={})

        key2 = default_key_builder(sample_func, namespace="namespace2", args=(1,), kwargs={})

        assert key1.startswith("namespace1:")
        assert key2.startswith("namespace2:")
        assert key1 != key2

    def test_empty_namespace(self):
        def sample_func():
            pass

        key = default_key_builder(sample_func, namespace="", args=(), kwargs={})

        assert key.startswith(":")

    def test_complex_types_in_args(self):
        def sample_func():
            pass

        # Test with various complex types
        key1 = default_key_builder(
            sample_func, namespace="test", args=([1, 2, 3], {"a": 1}, (1, 2)), kwargs={"nested": {"key": "value"}}
        )

        key2 = default_key_builder(
            sample_func, namespace="test", args=([1, 2, 3], {"a": 1}, (1, 2)), kwargs={"nested": {"key": "value"}}
        )

        assert key1 == key2

        # Different nested structure
        key3 = default_key_builder(
            sample_func,
            namespace="test",
            args=([1, 2, 3], {"a": 2}, (1, 2)),  # Changed dict value
            kwargs={"nested": {"key": "value"}},
        )

        assert key1 != key3
