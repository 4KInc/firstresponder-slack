from slack_sdk.models.blocks import (
    Block,
    ContextActionsBlock,
    FeedbackButtonObject,
    FeedbackButtonsElement,
)


def build_feedback_blocks() -> list[Block]:
    return [
        ContextActionsBlock(
            elements=[
                FeedbackButtonsElement(
                    action_id="feedback",
                    positive_button=FeedbackButtonObject(
                        text="Helpful",
                        accessibility_label="Submit positive feedback",
                        value="good-feedback",
                    ),
                    negative_button=FeedbackButtonObject(
                        text="Not Helpful",
                        accessibility_label="Submit negative feedback",
                        value="bad-feedback",
                    ),
                )
            ]
        )
    ]
