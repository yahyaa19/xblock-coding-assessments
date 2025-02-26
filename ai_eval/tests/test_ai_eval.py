"""
Testing module.
"""
# pylint: disable=redefined-outer-name,protected-access

import pytest
from xblock.exceptions import JsonHandlerError
from xblock.field_data import DictFieldData
from xblock.test.toy_runtime import ToyRuntime

from ai_eval import CodingAIEvalXBlock, ShortAnswerAIEvalXBlock
from ai_eval.base import AIEvalXBlock
from ai_eval.llm import SupportedModels


@pytest.fixture
def coding_block_data():
    """Fixture for coding block test data."""
    return {
        "language": "Python",
        "question": "ca va?",
        "code": "",
        "ai_evaluation": "",
        "code_exec_result": {},
        "marked_html": '<!doctype html>\n<html lang="en">\n<head></head>\n<body>\n    <script '
        'type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/marked/13.0.2/marked'
        '.min.js"></script>\n</body>\n</html>',
        "monaco_html": '<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n'
        '  <title>Monaco Editor</title>\n</head>\n<body style="margin: 0;">\n  <div class="monaco"'
        ' style="width: 100vw; height: 100vh;"></div>\n  <script type="module">\n    import * as'
        ' monaco from "https://cdn.jsdelivr.net/npm/monaco-editor@0.49.0/+esm";\n\n    window.editor '
        '= monaco.editor.create(document.querySelector(".monaco"), {\n      language: "python",\n    '
        "  minimap: { enabled: false },\n      lineNumbersMinChars: 2,\n      folding: false,\n    });\n\n"
        "    window.parent.postMessage('__USAGE_ID_PLACEHOLDER__', '*');\n  </script>\n</body>\n</html>\n",
    }


@pytest.fixture
def shortanswer_block_data():
    """Fixture for short answer block test data."""
    return {
        "question": "ca va?",
        "messages": {"USER": [], "LLM": []},
        "max_responses": 3,
        "marked_html": (
            '<!doctype html>\n<html lang="en">\n<head></head>\n<body>\n'
            '    <script type="text/javascript" '
            'src="https://cdnjs.cloudflare.com'
            '/ajax/libs/marked/13.0.2/marked.min.js"></script>\n'
            "</body>\n</html>"
        ),
    }


@pytest.fixture
def ai_eval_block():
    """Fixture for basic AIEvalXBlock."""
    runtime = ToyRuntime()
    block = AIEvalXBlock(
        runtime,
        DictFieldData(
            {
                "model": SupportedModels.GPT4O.value,
                "model_api_key": "",
            }
        ),
        None,
    )
    return block


def test_coding_block_student_view(coding_block_data):
    """Test the basic view loads for CodingAIEvalXBlock."""
    block = CodingAIEvalXBlock(ToyRuntime(), DictFieldData(coding_block_data), None)
    frag = block.student_view()
    assert coding_block_data == frag.json_init_args
    assert '<div class="eval-ai-container">' in frag.content


def test_shortanswer_block_student_view(shortanswer_block_data):
    """Test the basic view loads for ShortAnswerAIEvalXBlock."""
    block = ShortAnswerAIEvalXBlock(ToyRuntime(), DictFieldData(shortanswer_block_data), None)
    frag = block.student_view()
    assert frag.json_init_args == shortanswer_block_data
    assert '<div class="shortanswer_block">' in frag.content


def test_shortanswer_reset_allowed(shortanswer_block_data):
    """Test the reset function when allowed."""
    data = {
        **shortanswer_block_data,
        "allow_reset": True,
        "messages": {"USER": ["Hello"], "LLM": ["Hello"]},
    }
    block = ShortAnswerAIEvalXBlock(ToyRuntime(), DictFieldData(data), None)
    block.reset.__wrapped__(block, data={})
    assert block.messages == {"USER": [], "LLM": []}


def test_shortanswer_reset_forbidden(shortanswer_block_data):
    """Test the reset function when forbidden."""
    data = {
        **shortanswer_block_data,
        "messages": {"USER": ["Hello"], "LLM": ["Hello"]},
    }
    block = ShortAnswerAIEvalXBlock(ToyRuntime(), DictFieldData(data), None)
    with pytest.raises(JsonHandlerError):
        block.reset.__wrapped__(block, data={})
    assert block.messages == {"USER": ["Hello"], "LLM": ["Hello"]}


def test_character_image(shortanswer_block_data):
    """Test the character image."""
    data = {
        **shortanswer_block_data,
        "character_image": "/static/image.jpg",
    }
    block = ShortAnswerAIEvalXBlock(ToyRuntime(), DictFieldData(data), None)
    frag = block.student_view()
    assert '<img src="/static/image.jpg" />' in frag.content
