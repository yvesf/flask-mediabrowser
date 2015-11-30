import mediabrowser.ffmpeg as ffmpeg

import os
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