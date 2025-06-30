from pathlib import Path
import sys

# Add project root to sys.path for test imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Provide a minimal stub for the requests module if not installed
if "requests" not in sys.modules:
    import types

    requests_stub = types.SimpleNamespace(get=None)
    sys.modules["requests"] = requests_stub

# Stub heavy optional dependencies so importing the package works
if "numpy" not in sys.modules:
    import types

    numpy_stub = types.SimpleNamespace(
        array=lambda *a, **k: None,
        zeros=lambda *a, **k: 0,
        dot=lambda *a, **k: 0,
        linalg=types.SimpleNamespace(norm=lambda x: 0),
    )
    sys.modules["numpy"] = numpy_stub

if "sentence_transformers" not in sys.modules:
    import types

    class DummyModel:
        def encode(self, *a, **k):
            return 0

        def get_sentence_embedding_dimension(self):
            return 1

    sentence_stub = types.ModuleType("sentence_transformers")
    sentence_stub.SentenceTransformer = lambda *a, **k: DummyModel()
    sys.modules["sentence_transformers"] = sentence_stub
