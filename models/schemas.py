'''
데이터 구조가 불안정함.
Dataclass로 변환할것. 코드 수정 필요
'''

from typing import TypedDict, NotRequired

class CaptureInfo(TypedDict):
    time: float
    interval: list[float]
    capture_url: str
    caption: str
    capture_filename: str
    sound_url: NotRequired[str]

ClassDuration = TypedDict(
    "ClassDuration",
    {
        "class": str,
        "intervals": list[list[float]],
        "total_duration": float,
        "capture": list[CaptureInfo],
    }
)

AudioClipInfo = TypedDict(
    "AudioClipInfo",
    {
        "class": str,
        "path": str,
        "start_time": float,
        "duration": float
    }
)

ClassIntervals = dict[str, list[list[float]]]
CaptureImages = dict[str, list[CaptureInfo]]