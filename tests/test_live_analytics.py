import os
import pytest
from agent import ask
from agent.config import get_settings

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get('RUN_LIVE_LLM_TESTS') != '1' or not get_settings().groq_api_key,
    reason='Live Groq tests require RUN_LIVE_LLM_TESTS=1 and GROQ_API_KEY')]


@pytest.mark.parametrize('question,expected',[
    ('Who scored the first hat-trick?', 'Erling Haaland'),
    ('Who scored the second hat-trick?', 'Noni Madueke'),
    ('Who scored the third hat-trick?', 'Erling Haaland'),
    ('Who was the second player to reach 5 goals in the available reports?', '2024-09-21'),
    ('Who was the second player to reach 10 goals in the available reports?', 'Mohamed Salah'),
    ('Who was the third player to reach 10 goals in the available reports?', 'Cole Palmer'),
    ('Who scored the second hat-trick, and against which team?', 'Wolverhampton'),
])
def test_live_analysis(question,expected):
    assert expected.casefold() in ask(question,max_len=6000).casefold()
