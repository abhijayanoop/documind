from documind.config import settings

_ENABLED = bool(settings.langfuse_public_key and settings.langfuse_secret_key)

if _ENABLED:
    from langfuse.decorators import observe, langfuse_context

    def is_enabled() -> bool:
        return True

    def update_current_observation(**kwargs) -> None:
        langfuse_context.update_current_observation(**kwargs)

else:
    def observe(*dargs, **dkwargs):
        def decorator(fn):
            return fn
        if len(dargs) == 1 and callable(dargs[0]) and not dkwargs:
            return dargs[0]
        return decorator

    def is_enabled() -> bool:
        return False

    def update_current_observation(**kwargs) -> None:
        pass