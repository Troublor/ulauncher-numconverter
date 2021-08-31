from __future__ import annotations
import re
from abc import abstractmethod, ABC
from enum import Enum
from typing import List, Optional, Literal, Tuple, Union

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
import ulauncher.api.shared.event as events
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction


class DemoExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(events.KeywordQueryEvent, KeywordQueryEventListener())


class Number(ABC):
    @classmethod
    def parse(cls, payload: str, encoding: Encoding) -> Union[Number, ExtensionResultItem]:
        if len(payload) == 0:
            return ExtensionResultItem(
                icon='images/icon.png',
                name='No input',
                description=f"Please input a {encoding} number",
                on_enter=DoNothingAction(),
            )
        try:
            value = encoding.decode(payload)
            return Number(value)
        except ValueError:
            msg = "Failed to convert number"
            description = f"Value {payload} is not a {encoding} number."
            return ExtensionResultItem(
                icon='images/icon.png',
                name=msg,
                description=description,
                on_enter=DoNothingAction(),
                on_alt_enter=DoNothingAction(),
            )

    def __init__(self, value: int):
        self.value = value

    def result_item(self, encoding: Encoding) -> ExtensionResultItem:
        payload = encoding.encode(self.value)
        return ExtensionResultItem(
            icon=encoding.icon,
            name=payload,
            description=encoding.__str__().capitalize() + '; Copy to clipboard.',
            on_enter=CopyToClipboardAction(payload),
            on_alt_enter=CopyToClipboardAction(payload),
        )


class Encoding:
    @abstractmethod
    def base(self) -> int:
        pass

    @property
    def icon(self) -> str:
        return 'images/icon.png'

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def encode(self, value: int) -> str:
        pass

    def decode(self, value: str) -> int:
        return int(value, self.base())


class Hexadecimal(Encoding):
    def base(self) -> int:
        return 16

    @property
    def icon(self) -> str:
        return 'images/hex.png'

    def __str__(self):
        return "hexadecimal"

    def encode(self, value: int) -> str:
        return hex(value)[2:]


class Decimal(Encoding):
    def base(self) -> int:
        return 10

    @property
    def icon(self) -> str:
        return 'images/dec.png'

    def __str__(self):
        return "decimal"

    def encode(self, value: int) -> str:
        return str(value)


class Binary(Encoding):
    def base(self) -> int:
        return 2

    @property
    def icon(self) -> str:
        return 'images/bin.png'

    def __str__(self):
        return "binary"

    def encode(self, value: int) -> str:
        return bin(value)[2:]


class KeywordQueryEventListener(EventListener):

    def on_event(self, event: events.KeywordQueryEvent, extension: Extension):
        arg = event.get_argument() or ""
        value = re.split(r"\s+", arg)[0]
        kw = event.get_keyword()
        if kw == extension.preferences["kw_hex"]:
            num = Number.parse(value, Hexadecimal())
            encodings = [Decimal(), Binary()]
        elif kw == extension.preferences["kw_bin"]:
            num = Number.parse(value, Binary())
            encodings = [Decimal(), Hexadecimal()]
        elif kw == extension.preferences["kw_dec"]:
            num = Number.parse(value, Decimal())
            encodings = [Hexadecimal(), Binary()]
        else:
            raise RuntimeError()

        if isinstance(num, ExtensionResultItem):
            items = [num]
        else:
            items = list(map(lambda enc: num.result_item(enc), encodings))
        return RenderResultListAction(items)


if __name__ == '__main__':
    DemoExtension().run()
