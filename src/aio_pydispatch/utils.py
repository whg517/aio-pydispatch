"""Utils"""
import weakref
from typing import Any, Callable, Tuple
from weakref import ReferenceType, WeakMethod


def ref_adapter(receiver: Any) -> Tuple[Any, ReferenceType]:
    """
    Adapt a receiver to ref object.
    :param receiver:
    :return:
    """
    ref = weakref.ref
    receiver_obj = receiver

    # Check if receiver is a ref.
    if hasattr(receiver, '__self__') and hasattr(receiver, '__func__'):
        ref = WeakMethod
        receiver_obj = receiver.__self__
    referenced_receiver = ref(receiver)

    return receiver_obj, referenced_receiver


def safe_ref(receiver: Any, callback: Callable[..., None], *args, **kwargs) -> ReferenceType:
    """
    Save ref a receiver.
    Register a callback function to the object finalizer
    :param receiver:    A ref object
    :param callback:    Register the callback function to the object finalizer
    :param args:    Callback args
    :param kwargs:  Callback kwargs
    :return:
    """
    receiver_obj, receiver = ref_adapter(receiver)
    weakref.finalize(receiver_obj, callback, *args, **kwargs)
    return receiver


def id_maker(receiver: Any) -> int:
    """
    Get receiver id.
    If receiver is ref object, will return a ref object id.
    :param receiver:
    :return: Any
    """
    if not isinstance(receiver, ReferenceType):
        _, receiver = ref_adapter(receiver)
    return id(receiver)
