"""Evidence investigation with a user-selected model."""
from .core import RequirementContext, Brief

__all__ = ["RequirementContext", "Brief"]


def analyze(requirement, repo=".", *, model=None, excludes=(), max_evidence=8, max_rounds=4, retrieval_only=False, documents=(), snapshot=None, refresh=False):
    """One-call model investigation; endpoint settings may come from environment."""
    if model is None and not retrieval_only:
        model = ChatModel.from_env()
    with RequirementContext(repo, model=None if retrieval_only else model, excludes=excludes, documents=documents,cache=snapshot) as context:
        if refresh:
            context.refresh()
        return context.analyze(requirement, max_evidence=max_evidence, max_rounds=max_rounds)

from .models import ChatModel
__all__.extend(["analyze", "ChatModel"])

from .documents import SourceDocument
__all__.append("SourceDocument")
