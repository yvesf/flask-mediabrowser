import mediabrowser.ffmpeg as ffmpeg

import os
import tempfile
from pprint import pprint
from unittest import TestCase


class TestFfmpeg(TestCase):

    def setUp(self):
        self.test_mkv = os.path.join(os.path.dirname(__file__),
            "data", "test.mkv")


    # def test_data(self):
    #     data = ffmpeg.ffprobe_data(self.test_mkv)
    #     assert 'streams' in data
    #     assert len(data['streams']) == 2
    #
    #     assert 'format' in data
    #     assert 'duration' in data['format']
    #     assert data['format']['duration'] == '27.472000'

    def test_calculate_splittimes(self):
        for time in ffmpeg.calculate_splittimes(self.test_mkv, 120):
            print(time)

    def test_split(self):
        _, pos1 = ffmpeg.find_next_keyframe(self.test_mkv, 2, 5)
        frame_dur1, pos2 = ffmpeg.find_next_keyframe(self.test_mkv, pos1+2, 5)
        frame_dur2, pos3 = ffmpeg.find_next_keyframe(self.test_mkv, pos2+2, 5)
        out1 = open(tempfile.mktemp(), "wb")
        out2 = open(tempfile.mktemp(), "wb")
        pprint(locals())

        out1.write(ffmpeg.stream(self.test_mkv, pos1, pos2-pos1-frame_dur1).stdout.read())
        out2.write(ffmpeg.stream(self.test_mkv, pos2, pos3-pos2-frame_dur2).stdout.read())

        

        os.remove(out1.name)
        os.remove(out2.name)

