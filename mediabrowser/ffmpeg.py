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
    process = LoggedPopen(['ffprobe', '-v', 'fatal', '-print_format', 'json',
                           '-show_format', '-show_streams', ospath], stdout=PIPE, stderr=DEVNULL)
    data = json.load(utf8reader(process.stdout))
    assert process.wait() == 0, "ffprobe failed"
    process.stdout.close()
    return data


def stream(ospath, ss, t):
    logging.info('start ffmpeg stream h264 480p on path=%s ss=%s t=%s', ospath, ss, t)
    t_2 = t + 2.0
    output_ts_offset = ss
    cutter = LoggedPopen(
        shlex.split("ffmpeg -v fatal -ss {ss:.6f} -i ".format(**locals())) +
        [ospath] +
        shlex.split("-c:a aac -strict experimental -ac 2 -b:a 64k"
                    " -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.0 -preset ultrafast -trellis 0"
                    " -crf 31 -vf scale=w=trunc(oh*a/2)*2:h=480"
                    " -f mpegts"
                    " -output_ts_offset {output_ts_offset:.6f} -t {t:.6f} pipe:%d.ts".format(**locals())),
        stdout=PIPE)
    return cutter


def find_next_keyframe(ospath, start, max_offset):
    """
    :param: start: start search pts as float '123.123'
    :param: max_offset: max offset after start as float
    :return: (prev_duration, pts):
                    prev_duration: duration of the frame previous to the found key-frame
                    pts: PTS of next iframe but not search longer than max_offset
    :raise: Exception if no keyframe found
    """
    logging.info("start ffprobe to find next i-frame from {}".format(start))
    if start == 0.0:
        logging.info("return (0.0, 0.0) for start == 0.0")
        return 0.0, 0.0
    process = LoggedPopen(
        shlex.split("ffprobe -read_intervals {start:.6f}%+{max_offset:.6f} -show_frames "
                    "-select_streams v -print_format flat".format(**locals())) + [ospath],
        stdout=PIPE, stderr=DEVNULL)
    data = {'frame': None}
    prev_duration = None
    try:
        line = process.stdout.readline()
        while line:
            frame, name, value = re.match('frames\\.frame\\.(\d+)\\.([^=]*)=(.*)', line.decode('ascii')).groups()
            if data['frame'] != frame:
                data.clear()
                prev_duration = None
                data['frame'] = frame

            data[name] = value

            if 'pkt_duration_time' in data:
                prev_duration = float(data['pkt_duration_time'][1:-1])

            if 'key_frame' in data and data['key_frame'] == '1' and prev_duration is not None:
                if 'pkt_pts_time' in data and data['pkt_pts_time'][1:-1] != 'N/A' and float(
                        data['pkt_pts_time'][1:-1]) > start:
                    logging.info("Found pkt_pts_time={} prev__duration={}".format(data['pkt_pts_time'], prev_duration))
                    return prev_duration, float(data['pkt_pts_time'][1:-1])
                elif 'pkt_dts_time' in data and data['pkt_dts_time'][1:-1] != 'N/A' and float(
                        data['pkt_dts_time'][1:-1]) > start:
                    logging.info("Found pkt_dts_time={} prev_duration={}".format(data['pkt_dts_time'], prev_duration))
                    return prev_duration, float(data['pkt_dts_time'][1:-1])

            line = process.stdout.readline()
        raise Exception("Failed to find next i-frame in {} .. {} of {}".format(start, start + max_offset, ospath))
    finally:
        process.stdout.close()
        process.terminate()


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
    for (point, nextPoint) in zip([0.0] + points, points + [duration]):
        yield ("{:0.6f}".format(point), "{:0.6f}".format(nextPoint - point))


def thumbnail(ospath, width, height):
    process = LoggedPopen(shlex.split("ffmpeg -noaccurate_seek -ss 25.0 -i") + [ospath] +
                          shlex.split("-frames:v 10 -map 0:0"
                                      " -filter:v 'scale=w=oh*a:h={}, crop=(min(iw\,{})):(min(ih\,{}))'"
                                      " -f singlejpeg pipe:".format(height+(height/10), width, height)),
                          stdout=PIPE)
    return process


def thumbnail_video(ospath, width, height):
    duration = float(ffprobe_data(ospath)['format']['duration'])

    command = shlex.split("ffmpeg -v fatal")
    chunk_startpos = range(min(int(duration)-1,30), int(duration), 500)
    for pos in chunk_startpos:
        command += ["-ss", "{:.6f}".format(pos), "-t", "2", "-i", ospath]

    filter = " ".join(map(lambda i: "[{}:0]".format(i), range(len(chunk_startpos))))
    filter += " concat=n={}:v=1:a=0 [v1]".format(len(chunk_startpos))
    filter += "; [v1] fps=14 [v2]"
    filter += "; [v2] scale='w=trunc(oh*a/2)*2:h={}' [v3]".format(height + 6)
    filter += "; [v3] crop='min({},iw):min({},ih)' [v4]".format(width, height)
    command += ['-filter_complex', filter, '-map', '[v4]']
    command += shlex.split("-c:v libvpx -deadline realtime -f webm pipe:")

    encoder = LoggedPopen(command, stdout=PIPE)
    return encoder.stdout