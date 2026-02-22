from PIL import ImageDraw

def draw_timer(draw, frame_index, total_frames, width, height):
    remaining = total_frames - frame_index
    seconds = remaining // 30 + 1

    # top countdown number
    draw.text(
        (width//2, 250),
        str(seconds),
        fill=(255,255,255),
        anchor="mm"
    )

    # progress bar
    bar_w = int(width * 0.7)
    x0 = (width - bar_w)//2
    y = 320

    progress = frame_index / total_frames
    current_w = int(bar_w * (1-progress))

    draw.rectangle((x0, y, x0+bar_w, y+14), fill=(60,60,60))
    draw.rectangle((x0, y, x0+current_w, y+14), fill=(0,220,255))
