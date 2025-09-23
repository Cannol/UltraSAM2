import os
import logging
import subprocess
from typing import List
import json, yaml
import hashlib
import cv2

# from sam2.utils.storage import DataBlock
from sam2.configs import Q, Path

def video_reader_async(video_file, datapool_name):
    pass



IMAGE_FORMATS = ('.jpeg', '.jpg', '.gif', '.png', '.bmp', '.tiff', '.tif')

def read_sequence(seq_dir, abs_name=True, full_path=True, reverse=False) -> List[str]:
    """ :param seq_dir: The directory that contains a bunch of images in any picture format (.png, .jpg, ...)
        :param abs_name: If true, the picture name will be transferred to float type to sort
        :param full_path: If true, the picture name will be stored with full-absolute path, else it is only picture name
        :param reverse: If true, the sequence is returned with reversed order
        :return: A list of absolute paths/image names to all images in seq_dir (sorted by name)
    """
    if os.path.exists(seq_dir):
        imgs = [f for f in os.listdir(seq_dir) if f.lower().endswith(IMAGE_FORMATS)]
        if len(imgs) == 0:
            raise FileNotFoundError('No images found in {}!'.format(seq_dir))
        if abs_name:
            imgs.sort(key=lambda f: float(os.path.splitext(f)[0]), reverse=reverse)
        else:
            imgs.sort(reverse=reverse)
        if full_path:
            return [os.path.join(seq_dir, f) for f in imgs]
        else:
            return imgs
    raise FileNotFoundError(f'seq_dir {seq_dir} not found!')

VIDEO_FORMATS = ('.mp4', '.avi', '.mov')
def read_video_with_opencv(video_file, using_cache=True) -> List[str]:
    return []

def __check_ffmpeg_package():
    res = subprocess.run(['dpkg', '-l', 'ffmpeg'], capture_output=True, text=True)
    find_package = False
    for r in res.stdout.splitlines():
        if r.startswith('ii '):
            name, version = r.split()[1:3]
            logging.debug(f'ffmpeg found {name} {version}')
            find_package = True
            break
    return find_package

def __get_code_with_filename(filename, code_range=None) -> str:
    if code_range is None:
        return hashlib.md5(filename.encode("utf-8")).hexdigest()
    elif isinstance(code_range, (tuple, list)):
        return hashlib.md5(filename.encode("utf-8")).hexdigest()[code_range[0]: code_range[1]]
    elif isinstance(code_range, int):
        return hashlib.md5(filename.encode("utf-8")).hexdigest()[:code_range]

def read_video_with_ffmpeg(video_file, using_cache=True) -> List[str]:
    """
    :param video_file: Full path to video file
    :param using_cache: If true, using png/jpg image file to store cached video frames, for faster reading,
           otherwise, the video frames are stored in a shared-memory-pool, for faster reading.
    :return:
    """
    if not os.path.isfile(video_file):
        raise FileNotFoundError(f'video_file {video_file} not found!')
    try:
        if __check_ffmpeg_package():
            import ffmpeg
        else:
            raise FileNotFoundError('ffmpeg not found! Please install ffmpeg package with apt-get tools!')
    except (ImportError, FileNotFoundError) as e:
        logging.error("ffmpeg configuration error. (reason: %s)" % e.args)
        logging.info("Back to use opencv as video decoder.")
        return read_video_with_opencv(video_file, using_cache=using_cache)

    if using_cache:
        seq_cache_dirname = __get_code_with_filename(video_file)
        full_cache_dir = (Q + f"{seq_cache_dirname}")
        if os.path.exists(full_cache_dir):
            pass
        else:
            os.makedirs(full_cache_dir)
            ffmpeg.input(video_file).output(f'{output_format}%06d).run()')
    else:
        pass

class UnsupportedFileFormat(RuntimeError):
    pass

class ReaderCollection(object):
    @classmethod
    def json(cls, filename):
        from collections import OrderedDict
        with open(filename) as f:
            contents = json.load(f, object_pairs_hook=OrderedDict)
        return contents

    @classmethod
    def yaml(cls, filename):
        with open(filename) as f:
            contents = yaml.safe_load(f)
        return contents

def _none_func(file_name):
    _, postfix = os.path.splitext(file_name)
    raise UnsupportedFileFormat(f"[{postfix}] in {file_name}")

def read_file_auto(file_name: [str, Path], **kwargs):
    if isinstance(file_name, Path):
        file_name = file_name.value()
    elif isinstance(file_name, str):
        pass
    else:
        raise TypeError(f"{type(file_name)}")
    if not os.path.exists(file_name):
        raise FileExistsError(file_name)

    _, postfix = os.path.splitext(file_name)
    func = getattr(ReaderCollection, postfix.lower()[1:], _none_func)

    return func(file_name, **kwargs)

Read = read_file_auto

if __name__ == '__main__':
    # print(read_sequence("/data/vot2022-longterm/sequences/bicycle/color", full_path=False))
    read_video("/data/test_tree/tree3.mp4")