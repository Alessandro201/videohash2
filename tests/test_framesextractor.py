import os

import pytest

from videohash2.exceptions import FFmpegNotFound, FramesExtractorOutPutDirDoesNotExist
from videohash2.framesextractor import FramesExtractor
from videohash2.utils import create_and_return_temporary_directory

script_path = os.path.dirname(os.path.realpath(__file__))


def test_all():
    video_path = os.path.join(script_path, os.path.pardir, "assets", "rocket.mkv")
    output_dir = create_and_return_temporary_directory()
    video_length = 52.3
    interval = 1
    ffmpeg_path = None
    FramesExtractor(
        video_path, output_dir, video_length, interval=interval, ffmpeg_path=ffmpeg_path
    )

    with pytest.raises(FileNotFoundError):
        video_path = os.path.join(script_path, "thisvideodoesnotexist.mp4")
        output_dir = create_and_return_temporary_directory()
        FramesExtractor(
            video_path, output_dir, video_length, interval=1, ffmpeg_path=None
        )

    with pytest.raises(FFmpegNotFound):
        video_path = os.path.join(script_path, os.path.pardir, "assets", "rocket.mkv")
        output_dir = create_and_return_temporary_directory()
        ffmpeg_path = os.path.join(output_dir, "ffmpeg")
        FramesExtractor(
            video_path, output_dir, video_length, interval=1, ffmpeg_path=ffmpeg_path
        )

    with pytest.raises(FramesExtractorOutPutDirDoesNotExist):
        video_path = os.path.join(script_path, "../assets/rocket.mkv")
        output_dir = os.path.join(script_path, "thisdirdoesnotexist/")
        FramesExtractor(
            video_path, output_dir, video_length, interval=1, ffmpeg_path=None
        )
