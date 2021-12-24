"""Utils"""
import inspect
import weakref
from typing import Any, Callable, TypeVar, Union

T = TypeVar('T')  # pylint: disable=invalid-name


def func_accepts_kwargs(func: Callable[..., Any]):
    """Return True if function 'func' accepts keyword arguments **kwargs."""
    parameters = list(inspect.signature(func).parameters.values())
    return any(p for p in parameters if p.kind == p.VAR_KEYWORD)


def ref_adapter(receiver: T) -> Union[T, weakref.ReferenceType]:
    """
    Adapt a receiver to ref object
    :param receiver:
    :return:
    """
    ref = weakref.ref
    receiver_obj = receiver

    # Check if receiver is a ref.
    if hasattr(receiver, '__self__') and hasattr(receiver, '__func__'):
        ref = weakref.WeakMethod
        receiver_obj = receiver.__self__
    referenced_receiver = ref(receiver)

    return receiver_obj, referenced_receiver


def safe_ref(
        receiver: Callable[..., Any],
        callback: Callable[..., None]
) -> weakref.ReferenceType:
    """
    Save ref a receiver, and return a weak reference object.
    Register a callback function to the object finalizer
    :param receiver:    A callable object
    :param callback:    Register the callback function to the object finalizer.
                        We do not provide positional parameters, you should use high
                        level function, like ``functools.partial``.
    :return:
    """
    receiver_obj, receiver = ref_adapter(receiver)
    weakref.finalize(receiver_obj, callback)
    return receiver


def id_maker(target: Any) -> int:
    """
    Get receiver id.
    If receiver is ref object, will return a ref object id
    :param target:
    :return: int
    """
    if callable(target) and not isinstance(target, weakref.ReferenceType):
        _, target = ref_adapter(target)
    return id(target)
