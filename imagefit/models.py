from __future__ import division
from imagefit.conf import ext_to_format, settings
from PIL import Image as PilImage
from PIL import ImageOps

import mimetypes
try:
    import BytesIO
except ImportError:
    from io import BytesIO
import re
import os


class Image(object):
    """
    Represents an Image file on the system.
    """

    def __init__(self, path, cache=None, cached_name=None, *args, **kwargs):
        self.path = path
        self.pil = PilImage.open(path)
        self.cache = cache
        self.cached_name = cached_name

        # force RGB
        if self.pil.mode not in ('L', 'RGB', 'LA', 'RGBA'):
            self.pil = self.pil.convert('RGB')

    @property
    def mimetype(self):
        return mimetypes.guess_type(self.path)[0]

    @property
    def modified(self):
        return os.path.getmtime(self.path)

    @property
    def is_cached(self):
        return self.cache and self.cached_name in self.cache

    def resize(self, width=None, height=None):
        return self.pil.thumbnail(
            (int(width), int(height)),
            PilImage.ANTIALIAS)

    def crop(self, width=None, height=None):
        img_w, img_h = self.pil.size
        # don't crop an image than is smaller than requested size
        if img_w < width and img_h < height:
            return self.pil
        elif img_w < width:
            width = img_w
        elif img_h < height:
            height = img_h
        delta_w = img_w / width
        delta_h = img_h / height
        delta = delta_w if delta_w < delta_h else delta_h
        new_w = img_w / delta
        new_h = img_h / delta
        self.resize(new_w, new_h)
        box_diff = ((new_w - width) / 2, (new_h - height) / 2)
        box = (
            int(box_diff[0]), int(box_diff[1]), int(new_w - box_diff[0]),
            int(new_h - box_diff[1]))
        self.pil = self.pil.crop(box)
        return self.pil
    
    def cropbox(self, width=None, height=None, fill=None):
        img = self.pil
        target_width = width
        target_height = height
        if img.format == "PNG":
            fill = "rgba(0, 0, 0, 0)"
        widthPercent = (width / float(img.size[0]))
        if widthPercent >= 1.0:
            return img

        height = int((float(img.size[1]) * float(widthPercent)))
        self.pil = img.resize((width, height), PilImage.ANTIALIAS)

        w, h = self.pil.size
        left = top = right = bottom = 0
        if target_width > w:
            delta = target_width - w
            left = delta // 2
            right = delta - left

        if target_height > h:
            delta = target_height - h
            top = delta // 2
            bottom = delta - top

        self.pil = ImageOps.expand(self.pil, border=(left, top, right, bottom), fill=fill)
        return self.pil

    def render(self):
        """
        Renders the file content
        """
        if self.is_cached:
            return self.cache.get(self.cached_name)
        else:
            image_str = BytesIO()
            self.pil.save(image_str, ext_to_format(self.cached_name))
            return image_str.getvalue()

    def save(self):
        """
        Save the image to the cache if provided and not cached yet.
        """
        if self.cache and not self.is_cached:
            image_str = BytesIO()
            self.pil.save(image_str, ext_to_format(self.cached_name))
            self.cache.set(self.cached_name, image_str.getvalue())
            image_str.close()


class Presets(object):
    """
    Representation of an image format storage
    """

    @classmethod
    def get_all(cls):
        """
        Reads presets from settings
        """
        return getattr(settings, 'IMAGEFIT_PRESETS', {})

    @classmethod
    def get(cls, key, to_tuple=False):
        """
        Retrieves a specific preset by its name
        """
        preset = cls.get_all().get(key, None)
        return preset

    @classmethod
    def has(cls, key):
        """
        Checks if a preset exists
        """
        return key in cls.get_all()

    @classmethod
    def from_string(cls, string):
        # if re.match('(\d+)x(\d+),?(\w*)', string):
        #     sizes = [x for x in re.match(
        #         '(\d+)x(\d+)(,?[c|C]?)', string).groups()]
        #     return {
        #         'width': int(sizes[0]), 'height': int(sizes[1]),
        #         'crop': bool(sizes[2]),'cropbox': bool(sizes[3])
        #     }

        if re.match('(\d+)x(\d+),?(\w*),?(\w*),?(\w*)', string):
            cons = string.split(",")
            sizes = cons[0].split("x")
            list = {
                'width': int(sizes[0]), 'height': int(sizes[1]),
                'crop': False, 'cropbox': False
                ,'fill': 'white'
            }
            if len(cons) > 1:
                if cons[1] == 'C':
                    list['crop'] = True
                else:
                    list['cropbox'] = True
                if list['cropbox']:
                    try:
                        list['fill'] = "#" + cons[2]
                    except:
                        ""
            return list
