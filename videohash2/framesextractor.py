import math
import os
import re
import shlex
from shutil import which
from subprocess import DEVNULL, PIPE, Popen, check_output
from typing import Optional, Union

from .exceptions import (
    FFmpegError,
    FFmpegFailedToExtractFrames,
    FFmpegNotFound,
    FramesExtractorOutPutDirDoesNotExist
)

# python module to extract the frames from the input video.
# Uses the FFmpeg Software to extract the frames.


class FramesExtractor:
    """
    Extract frames from the input video file and save at the output directory(frame storage directory).
    """

    def __init__(
        self,
        video_path: str,
        output_dir: str,
        video_length: float,
        interval: Union[int, float] = 1,
        ffmpeg_path: Optional[str] = None,
    ) -> None:
        """
        Raises Exeception if video_path does not exists.
        Raises Exeception if output_dir does not exists or if not a directory.

        Checks  the ffmpeg installation and the path; thus ensure that we can use it.

        :return: None

        :rtype: NoneType

        :param video_path: absolute path of the video

        :param output_dir: absolute path of the directory
                           where to save the frames.

        :param interval: interval is seconds. interval must be an integer.
                         Extract one frame every given number of seconds.
                         Default is 1, that is one frame every second.

        :param ffmpeg_path: path of the ffmpeg software if not in path.

        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.video_length = video_length
        self.interval = interval
        self.ffmpeg_path = ""
        if ffmpeg_path:
            self.ffmpeg_path = ffmpeg_path

        if not os.path.exists(self.video_path):
            raise FileNotFoundError(
                f"No video found at '{self.video_path}' for frame extraction."
            )

        if not os.path.exists(self.output_dir):
            raise FramesExtractorOutPutDirDoesNotExist(
                f"No directory called '{self.output_dir}' found for storing the frames."
            )

        self._check_ffmpeg()

        self.extract()

    def _check_ffmpeg(self) -> None:
        """
        Checks the ffmpeg path and runs 'ffmpeg -version' to verify that the
        software, ffmpeg is found and works.

        :return: None

        :rtype: NoneType
        """

        if not self.ffmpeg_path:
            if not which("ffmpeg"):
                raise FFmpegNotFound(
                    "FFmpeg is not on the system path. Install FFmpeg and add it to the path."
                    + "Or you can also pass the path via the 'ffmpeg_path' parameter."
                )
            else:
                self.ffmpeg_path = str(which("ffmpeg"))

        # Check the ffmpeg
        try:
            # check_output will raise FileNotFoundError if it does not finds the ffmpeg
            output = check_output([str(self.ffmpeg_path), "-version"]).decode()

        except FileNotFoundError:
            raise FFmpegNotFound(f"FFmpeg not found at '{self.ffmpeg_path}'.")

        else:
            if "ffmpeg version" not in output:
                raise FFmpegError(
                    f"ffmpeg at '{self.ffmpeg_path}' is not really ffmpeg. Output of ffmpeg -version is \n'{output}'."
                )

    @staticmethod
    def detect_crop(
        video_path: Optional[str] = None,
        frames: int = 3,
        ffmpeg_path: Optional[str] = None,
        video_length: float = 2,
    ) -> list:
        """
        Detects the the amount of cropping to remove black bars.

        The method uses [ffmpeg.git] / libavfilter /vf_cropdetect.c
        to detect_crop for some fixed intervals.

        The mode of the detected crops is selected as the crop required.

        :return: FFmpeg argument -vf filter and confromable crop parameter.

        :rtype: str
        """

        # We look upto the 120th minute into the video to detect the most
        # precise crop value
        time_start_list = [
            2,
            5,
            10,
            20,
            40,
            100,
            300,
            600,
            1200,
            2400,
            7200,
            14400,
        ]

        crop_list = []

        for start_time in time_start_list:
            # Stopping the loop if we go beyond the end length of the video.
            # We round the video length up to make sure we do get the whole
            # video.
            if start_time > math.ceil(video_length):
                break

            command = f'"{ffmpeg_path}" -ss {start_time} -i "{video_path}" -vframes {frames} -vf cropdetect -f null -'

            process = Popen(
                shlex.split(command), stdin=DEVNULL, stdout=PIPE, stderr=PIPE
            )

            output, error = process.communicate()

            matches = re.findall(
                r"crop\=[1-9][0-9]{0,3}:[1-9][0-9]{0,3}:[0-9]{1,4}:[0-9]{1,4}",
                (output.decode() + error.decode()),
            )

            for match in matches:
                crop_list.append(match)

        mode = None
        if len(crop_list) > 0:
            mode = max(crop_list, key=crop_list.count)

        crop = []
        if mode:
            crop = ["-vf", mode]

        return crop

    def extract(self) -> None:
        """
        Extract the frames at every n seconds where n is the
        integer set to self.interval.

        :return: None

        :rtype: NoneType
        """

        ffmpeg_path = self.ffmpeg_path
        video_path = self.video_path
        video_length = self.video_length
        output_dir = self.output_dir

        if os.name == "posix":
            ffmpeg_path = shlex.quote(self.ffmpeg_path)
            video_path = shlex.quote(self.video_path)
            output_dir = shlex.quote(self.output_dir)

        crop = FramesExtractor.detect_crop(
            video_path=video_path,
            frames=3,
            ffmpeg_path=ffmpeg_path,
            video_length=video_length,
        )

        command = [
            str(ffmpeg_path),
            "-i",
            str(video_path),
            *crop,
            "-s",
            "144x144",
            "-r",
            str(self.interval),
            str(output_dir) + "video_frame_%07d.jpeg",
        ]

        process = Popen(command, stdin=DEVNULL, stdout=PIPE, stderr=PIPE)
        output, error = process.communicate()

        ffmpeg_output = output.decode()
        ffmpeg_error = error.decode()

        if len(os.listdir(self.output_dir)) == 0:
            raise FFmpegFailedToExtractFrames(
                f"FFmpeg could not extract any frames.\n{command}\n{ffmpeg_output}\n{ffmpeg_error}"
            )
