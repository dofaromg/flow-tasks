class AI3DPersonality:
    """Simple AI 3D personality module with basic emotional interaction.

    The module provides a minimal interface for setting an emotion and retrieving
    a textual expression describing the 3D avatar's face. It supports both
    English and Chinese responses.
    """

    _expressions = {
        "neutral": {"en": "neutral expression", "zh": "中性表情"},
        "happy": {"en": "smiling brightly", "zh": "燦爛微笑"},
        "sad": {"en": "looking sad", "zh": "悲傷表情"},
        "angry": {"en": "showing anger", "zh": "憤怒表情"},
    }

    DEFAULT_EMOTION = "neutral"
    SUPPORTED_LANGUAGES = ("en", "zh")

    def __init__(self, name: str):
        self.name = name
        self.emotion = self.DEFAULT_EMOTION

    def set_emotion(self, emotion: str) -> None:
        """Update the avatar's current emotion.

        Parameters
        ----------
        emotion: str
            One of ``neutral``, ``happy``, ``sad`` or ``angry``.
        """
        if emotion not in self._expressions:
            raise ValueError(
                f"Unsupported emotion: {emotion}. Valid emotions are: {', '.join(self._expressions.keys())}"
            )
        self.emotion = emotion

    def _validate_language(self, language: str) -> None:
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Language must be one of {self.SUPPORTED_LANGUAGES}")

    def get_expression(self, language: str = "en") -> str:
        """Return a textual description of the avatar's facial expression.

        Parameters
        ----------
        language: str
            ``en`` for English or ``zh`` for Chinese.
        """
        self._validate_language(language)
        return self._expressions[self.emotion][language]

    def interact(self, message: str, language: str = "en") -> str:
        """Generate a simple response reflecting the current emotion.

        Parameters
        ----------
        message: str
            User's input message.
        language: str
            ``en`` or ``zh`` to select the response language.
        """
        templates = {
            "en": "{name} ({emotion}) says: I hear you saying '{message}'.",
            "zh": "{name}（{emotion}）說：我聽到了你說『{message}』。",
        }
        self._validate_language(language)
        return templates[language].format(
            name=self.name,
            emotion=self._expressions[self.emotion][language],
            message=message,
        )


__all__ = ["AI3DPersonality"]
