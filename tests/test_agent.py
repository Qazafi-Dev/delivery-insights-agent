from delivery_insights_agent.agent import (
    GENERIC_REPLY,
    LIVE_TRACKING_REPLY,
    REFUND_REPLY,
    out_of_scope_reply,
)


def test_refund_question_gets_refund_reply():
    assert out_of_scope_reply("I want a refund") == REFUND_REPLY


def test_tracking_question_gets_tracking_reply():
    assert out_of_scope_reply("Where is my delivery driver?") == LIVE_TRACKING_REPLY


def test_unknown_question_gets_generic_reply():
    assert out_of_scope_reply("What is the weather?") == GENERIC_REPLY
