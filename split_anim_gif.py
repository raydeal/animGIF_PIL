# -*- encoding: utf-8 -*-
"""
The script splits animated GIF into images based on frames.
"""
from PIL import Image,ImageSequence
from ExtGifImagePlugin import *

def split_gif(gif_name):
  """Procedure splits animated GIF into images based on frames.
  
     duration,frames = split_gif('animated.gif')
  """
  im = Image.open(gif_name)
  duration = []
  frames_list = []
  if im.mode == 'P':
    palette = im.getpalette()
  non_transparent = Image.new('RGBA',im.size,(255,255,255,255))
  
	
  for frame in ImageSequence.Iterator(im):
    if frame.mode == 'P' and frame.info.get('transparency',0) > 0:
		  frame.putpalette(palette)
    duration.append(frame.info['duration']/1000.0)
    box = frame.info['frame_box']
    frame = frame.crop(box)
    frame = frame.convert("RGBA")
    non_transparent.paste(frame,box,frame)
    frames_list.append(non_transparent.convert('RGB').convert('P', dither=Image.NONE, palette=Image.ADAPTIVE))
  return duration,frames_list

def test():
  """Test procedure"""
  index = 0
  file_name=raw_input('GIF file name: ')
  duration,frames = split_gif(file_name)
  for new_frame in frames:
    new_frame.save('image_frame_'+str(index)+'.gif','GIF')
    index += 1

if __name__ == '__main__': test()
