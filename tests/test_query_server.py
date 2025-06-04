import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import types

# Stub the transformers pipeline to avoid loading a real model
transformers = types.ModuleType('transformers')
transformers.pipeline = lambda *args, **kwargs: (
    lambda prompt, max_length=None, num_return_sequences=None: [
        {"generated_text": prompt + " stub"}
    ]
)
sys.modules.setdefault('transformers', transformers)

from query_server import app, query, Question


def test_query_route_registered():
    assert any(r.path == '/query' and 'POST' in getattr(r, 'methods', []) for r in app.routes)


def test_query_function():
    result = query(Question(question='test'))
    assert 'answer' in result
    assert 'stub' in result['answer']

