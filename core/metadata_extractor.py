"""
元数据提取器 - 提取图片EXIF、PDF属性等
"""
import os
import json
from datetime import datetime
from typing import Optional, Tuple

from utils.logger import logger


def extract_image_metadata(file_path: str) -> dict:
    """提取图片EXIF元数据"""
    metadata = {}
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        img = Image.open(file_path)
        metadata['width'] = img.width
        metadata['height'] = img.height

        exif_data = img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    try:
                        metadata['photo_taken_time'] = datetime.strptime(
                            str(value), '%Y:%m:%d %H:%M:%S')
                    except (ValueError, TypeError):
                        pass
                elif tag == 'Model':
                    metadata['camera_model'] = str(value)[:100]
                elif tag == 'GPSInfo':
                    try:
                        gps = _parse_gps(value)
                        if gps:
                            metadata['gps_latitude'] = gps[0]
                            metadata['gps_longitude'] = gps[1]
                    except Exception:
                        pass
        img.close()
    except Exception as e:
        logger.debug(f"提取图片元数据失败: {file_path} - {e}")
    return metadata


def _parse_gps(gps_info) -> Optional[Tuple[float, float]]:
    """解析GPS信息"""
    try:
        def _to_degrees(value) -> float:
            d, m, s = value
            return float(d) + float(m) / 60.0 + float(s) / 3600.0

        lat = _to_degrees(gps_info[2])
        lon = _to_degrees(gps_info[4])

        if gps_info[1] == 'S':
            lat = -lat
        if gps_info[3] == 'W':
            lon = -lon
        return (lat, lon)
    except (KeyError, IndexError, TypeError):
        return None


def extract_pdf_metadata(file_path: str) -> dict:
    """提取PDF元数据"""
    metadata = {}
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        info = reader.metadata
        if info:
            if info.title:
                metadata['pdf_title'] = str(info.title)[:255]
            if info.author:
                metadata['pdf_author'] = str(info.author)[:100]
        metadata['pdf_pages'] = len(reader.pages)
    except Exception as e:
        logger.debug(f"提取PDF元数据失败: {file_path} - {e}")
    return metadata


def extract_video_metadata(file_path: str) -> dict:
    """提取视频基本信息（时长、分辨率、文件大小）
    优先使用 ffprobe（ffmpeg 套件），不可用时回退到仅文件大小。
    """
    import subprocess

    metadata = {}
    size = 0
    try:
        size = os.path.getsize(file_path)
    except Exception:
        pass

    # 尝试用 ffprobe 提取详细元数据
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                file_path,
            ],
            capture_output=True, text=True, timeout=15)

        if result.returncode == 0 and result.stdout:
            info = json.loads(result.stdout)

            # 时长
            fmt = info.get('format', {})
            duration = fmt.get('duration')
            if duration:
                try:
                    metadata['video_duration'] = int(float(duration))
                except (ValueError, TypeError):
                    pass

            # 分辨率（取第一个视频流）
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    w = stream.get('width')
                    h = stream.get('height')
                    if w and h:
                        metadata['video_resolution'] = f"{w}x{h}"
                    break
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        # ffprobe 不可用，静默回退
        pass
    except Exception as e:
        logger.debug(f"ffprobe 提取视频元数据失败: {file_path} - {e}")

    # 始终记录文件大小
    extra = {'file_size_bytes': size}
    if 'video_duration' in metadata:
        extra['duration_seconds'] = metadata['video_duration']
    if 'video_resolution' in metadata:
        extra['resolution'] = metadata['video_resolution']
    metadata['extra_data'] = json.dumps(extra)

    return metadata


def extract_metadata(file_path: str, file_type: str) -> dict:
    """根据文件类型自动选择提取方法"""
    if file_type == 'image':
        return extract_image_metadata(file_path)
    elif file_type == 'document':
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return extract_pdf_metadata(file_path)
    elif file_type == 'video':
        return extract_video_metadata(file_path)
    return {}
