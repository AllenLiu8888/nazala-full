
from .models import (
    Game, Turn, Option,
    ATTR_A_NAME, ATTR_B_NAME, ATTR_C_NAME, ATTR_D_NAME
)
from dataclasses import dataclass
from typing import List, Dict

KEY_OPTION_TEXT = "text"
KEY_OPTION_ATTRS = "attrs"


@dataclass
class LLMOptionAttributes:
    attr_a: int = 0
    attr_b: int = 0
    attr_c: int = 0
    attr_d: int = 0

    attr_a_name = ATTR_A_NAME
    attr_b_name = ATTR_B_NAME
    attr_c_name = ATTR_C_NAME
    attr_d_name = ATTR_D_NAME


@dataclass
class LLMOption:
    text: str
    attributes: LLMOptionAttributes
    

@dataclass
class LLMResponse:
    question: str
    options: List[LLMOption]


# Create mock data using the new classes
mock_attributes = LLMOptionAttributes(attr_a=20, attr_b=5, attr_c=-10, attr_d=-15)

mock_llm_response = LLMResponse(
    question="This is a mocked question from LLM.",
    options=[
        LLMOption(text="This is the description text for option A.", attributes=mock_attributes),
        LLMOption(text="This is the description text for option B.", attributes=mock_attributes),
        LLMOption(text="This is the description text for option C.", attributes=mock_attributes),
        LLMOption(text="This is the description text for option D.", attributes=mock_attributes),
    ]
)

def ask_first_question_from_llm() -> LLMResponse:
    # TODO: collect prompt from default prompt template
    #       to LLM to ask for the first question

    # TODO: send to LLM

    # TODO: deal with LLM Response

    # TODO: return the expected LLMResponse object
    return mock_llm_response


def ask_next_question_from_llm(turn: Turn) -> LLMResponse:
    # TODO: collect prompt from collect prompt to LLM to ask for the first question
    #       to LLM to ask for the first question x

    # TODO: send to LLM

    # TODO: deal with LLM Response

    # TODO: return the expected LLMResponse object
    return mock_llm_response


def create_turn_from_llm_response(game: Game, llm_response: LLMResponse) -> Turn:
    turn = Turn.create_by_game(game=game, question_text=llm_response.question)
    for _, option in enumerate(llm_response.options):
        Option.create_by_turn(
            turn=turn,
            text=option.text,
            attr_a=option.attributes.attr_a,
            attr_b=option.attributes.attr_b,
            attr_c=option.attributes.attr_c,
            attr_d=option.attributes.attr_d
        )
    return turn
