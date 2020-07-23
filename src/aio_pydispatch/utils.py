import weakref
from typing import Any, Callable, Tuple


def ref_adapter(receiver: Any) -> Tuple[Any, Any]:
    ref = weakref.ref
    receiver_obj = receiver

    # 检查 receiver 是不是对象引用
    if hasattr(receiver, '__self__') and hasattr(receiver, '__func__'):
        ref = weakref.WeakMethod
        receiver_obj = receiver.__self__
    receiver = ref(receiver)

    return receiver_obj, receiver


def safe_ref(receiver: Any, callback: Callable[[], None], *args, **kwargs) -> Any:
    receiver_obj, receiver = ref_adapter(receiver)
    weakref.finalize(receiver_obj, callback, *args, **kwargs)
    return receiver


def make_id(receiver: Any) -> int:
    if not isinstance(receiver, weakref.ReferenceType):
        _, receiver = ref_adapter(receiver)
    return id(receiver)
