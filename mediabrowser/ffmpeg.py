import json
import re
import codecs
import logging
from subprocess import Popen, PIPE, DEVNULL
import shlex

utf8reader = codecs.getreader('utf-8')


def LoggedPopen(command, *args, **kwargs):
    logging.info("Popen(command={} args={}) with kwargs={}".format(
        " ".join(map(repr, command)),
        " ".join(map(repr, args)),
        " ".join(map(repr, kwargs))))
    return Popen(command, *args, **kwargs)


def ffprobe_data(ospath):
    logging.info('ffprobe %s', ospath)
    process = LoggedPopen(['ffprobe', '-v', 'quiet', '-print_format', 'json',
                           '-show_format', '-show_streams', ospath], stdout=PIPE, stderr=DEVNULL)
    data = json.load(utf8reader(process.stdout))
    assert process.wait() == 0, "ffprobe failed"
    process.stdout.close()
    return data


def stream(ospath, ss, t):
    logging.info('start ffmpeg stream h264 480p on path=%s ss=%s t=%s', ospath, ss, t)
    t_2 = t + 2.0
    cutter = LoggedPopen(
        shlex.split("ffmpeg -ss {ss:.6f} -async 1 -i ".format(**locals())) +
        [ospath] +
        shlex.split("-c:a aac -strict experimental -ac 2 -b:a 44k"
                    ""
                    " -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.0 -preset ultrafast -trellis 0"
                    " -crf 31 -vf scale=w=trunc(oh*a/2)*2:h=360"
                    ""
                    " -f mpegts -output_ts_offset {ss:.6f} -t {t:.6f} pipe:%d.ts".format(**locals())),
        stdout=PIPE, stderr=DEVNULL)
    return cutter


def find_next_keyframe(ospath, start, max_offset):
    """
    :param: start: start search pts as float '123.123'
    :param: max_offset: max offset after start as float
    :return: PTS of next iframe but not search longer than max_offset
    """
    logging.info("start ffprobe to find next i-frame from {}".format(start))
    if start == 0.0:
        return 0.0
    process = LoggedPopen(
        shlex.split("ffprobe -read_intervals {start:.6f}%+{max_offset:.6f} -show_frames "
                    "-select_streams v -print_format flat".format(**locals())) + [ospath],
        stdout=PIPE, stderr=DEVNULL)
    data = {'frame': None}
    try:
        line = process.stdout.readline()
        while line:
            frame, name, value = re.match('frames\\.frame\\.(\d+)\\.([^=]*)=(.*)', line.decode('ascii')).groups()
            if data['frame'] != frame:
                data.clear()
                data['frame'] = frame

            data[name] = value
            if 'key_frame' in data and data['key_frame'] == '1':
                if 'pkt_pts_time' in data and data['pkt_pts_time'][1:-1] != 'N/A' and float(
                        data['pkt_pts_time'][1:-1]) > start:
                    logging.info("Found pkt_pts_time={}".format(data['pkt_pts_time']))
                    return float(data['pkt_pts_time'][1:-1])
                elif 'pkt_dts_time' in data and data['pkt_dts_time'][1:-1] != 'N/A' and float(
                        data['pkt_dts_time'][1:-1]) > start:
                    logging.info("Found pkt_dts_time={}".format(data['pkt_dts_time']))
                    return float(data['pkt_dts_time'][1:-1])

            line = process.stdout.readline()
        raise Exception("Failed to find next i-frame in {} .. {} of {}".format(start, max_offset, ospath))
    finally:
        process.stdout.close()
        process.terminate()
        logging.info("finished ffprobe to find next i-frame from {}".format(start))


def calculate_splittimes(ospath, chunk_duration):
    """
    :param ospath: path to media file
    :return: list of PTS times to split the media, in the form of
                    ((start1, duration1),  (start2, duration2), ...)
                    (('24.949000', '19.500000'),  ('44.449000', ...), ...)
            Note: - start2 is equal to start1 + duration1
                  - sum(durationX) is equal to media duration
    """

    def calculate_points(media_duration):
        pos = 10
        while pos < media_duration:
            yield pos
            pos += chunk_duration

    duration = float(ffprobe_data(ospath)['format']['duration'])
    points = list(calculate_points(duration))
    adj_points = points
    # for point in points:
    #     adj_points += [find_next_iframe(ospath, point, chunk_duration / 2.0)]
    #
    for (point, nextPoint) in zip([0.0] + adj_points, adj_points + [duration]):
        yield ("{:0.6f}".format(point), "{:0.6f}".format(nextPoint - point))


def thumbnail_png(path, size):
    logging.debug("thumbnail %s", path)
    process = LoggedPopen(['ffmpegthumbnailer', '-i', path,
                           '-o', '-', '-s', str(size), '-c', 'png'],
                          stdout=PIPE, stderr=DEVNULL)
    return process
