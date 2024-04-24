import numpy
from PIL import Image


def generate_shade_array(item, side):
    if side == 0:
        side = "front"
    else:
        side = "back"
    img = Image.open(f"templates/{item}_{side}.png")
    img = img.convert("RGB")

    d = img.getdata()
    shade_array = []

    # 0 - plain color, 1 - lighter shade, 2 - shade, 3 - outline
    for item in d:

        # change all white (also shades of whites)
        if item[0] in list(range(240, 256)):
            shade_array.append(0)
        elif item[0] in list(range(220, 240)):
            shade_array.append(1)
        elif item[0] in list(range(45, 220)):
            shade_array.append(2)
        else:
            shade_array.append(3)

    # shade_array = numpy.array(shade_array)
    return shade_array


arrs = {"shirt_front": generate_shade_array("shirt", 0), "shirt_back": generate_shade_array("shirt", 1)}
