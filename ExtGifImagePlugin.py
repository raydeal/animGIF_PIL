# -*- encoding: utf-8 -*-

from PIL import GifImagePlugin
import Image, ImageFile, ImagePalette

class ExtGifImageFile(GifImagePlugin.GifImageFile):
    format = "ExtGIF"

    def _open(self):
        # Screen
        s = self.fp.read(13)
        if s[:6] not in ["GIF87a", "GIF89a"]:
            raise SyntaxError, "not a GIF file"
        self.info["version"] = s[:6]
        self.size = GifImagePlugin.i16(s[6:]), GifImagePlugin.i16(s[8:])
        self.tile = []
        flags = ord(s[10])
        bits = (flags & 7) + 1
        if flags & 128:
            # get global palette
            self.info["background"] = ord(s[11])
            # check if palette contains colour indices
            p = self.fp.read(3<<bits)
            for i in range(0, len(p), 3):
                if not (chr(i/3) == p[i] == p[i+1] == p[i+2]):
                    p = ImagePalette.raw("RGB", p)
                    self.global_palette = self.palette = p
                    break
        self.__fp = self.fp
        self.__rewind = self.fp.tell()
        self.seek(0) # get ready to read first frame

    def seek(self, frame):
        if frame == 0:
            # rewind
            self.__offset = 0
            self.dispose = None
            self.__frame = -1
            self.__fp.seek(self.__rewind)
        if frame != self.__frame + 1:
            raise ValueError, "cannot seek to frame %d" % frame
        self.__frame = frame
        self.tile = []
        self.fp = self.__fp
        if self.__offset:
            # backup to last frame
            self.fp.seek(self.__offset)
            while self.data():
                pass
            self.__offset = 0
        if self.dispose:
            self.im = self.dispose
            self.dispose = None
        self.palette = self.global_palette
        while 1:
            s = self.fp.read(1)
            if not s or s == ";":
                break
            elif s == "!":
                #
                # extensions
                #
                s = self.fp.read(1)
                block = self.data()
                if ord(s) == 249:
                    #
                    # graphic control extension
                    #
                    flags = ord(block[0])
                    if flags & 1:
                        self.info["transparency"] = ord(block[3])
                    self.info["duration"] = GifImagePlugin.i16(block[1:3]) * 10
                    try:
                        # disposal methods
                        if flags & 8:
                            # replace with background colour
                            self.dispose = Image.core.fill("P", self.size,
                                self.info["background"])
                        elif flags & 16:
                            # replace with previous contents
                            self.dispose = self.im.copy()
                    except (AttributeError, KeyError):
                        pass
                elif ord(s) == 255:
                    #
                    # application extension
                    #
                    self.info["extension"] = block, self.fp.tell()
                    if block[:11] == "NETSCAPE2.0":
                        block = self.data()
                        if len(block) >= 3 and ord(block[0]) == 1:
                            self.info["loop"] = GifImagePlugin.i16(block[1:3])
                while self.data():
                    pass
            elif s == ",":
                #
                # local image
                #
                s = self.fp.read(9)
                # extent
                x0, y0 = GifImagePlugin.i16(s[0:]), GifImagePlugin.i16(s[2:])
                x, y = GifImagePlugin.i16(s[4:]), GifImagePlugin.i16(s[6:])
                x1, y1 = x0 + x, y0 + y
                self.info['frame_box'] = (x0,y0,x1,y1)
                flags = ord(s[8])
                interlace = (flags & 64) != 0
                if flags & 128:
                    bits = (flags & 7) + 1
                    self.palette =\
                        ImagePalette.raw("RGB", self.fp.read(3<<bits))

                # image data
                bits = ord(self.fp.read(1))
                self.__offset = self.fp.tell()
                self.tile = [("gif",
                             (x0, y0, x1, y1),
                             self.__offset,
                             (bits, interlace))]
                break
            else:
                pass
                # raise IOError, "illegal GIF tag `%x`" % ord(s)
        if not self.tile:
            # self.__fp = None
            raise EOFError, "no more images in GIF file"
        self.mode = "L"
        if self.palette:
            self.mode = "P"

# --------------------------------------------------------------------
# Registry
Image.register_open(ExtGifImageFile.format, ExtGifImageFile, GifImagePlugin._accept)
Image.register_save(ExtGifImageFile.format, GifImagePlugin._save)
Image.register_extension(ExtGifImageFile.format, ".gif")
Image.register_mime(ExtGifImageFile.format, "image/gif")
