import json

from PIL import Image
import cv2
from io import BytesIO
from aiogram.types import BufferedInputFile
import rembg
import numpy
import calculate_shades

template_sizes = {"shirt": (1099, 1389)}
shade_factor = 0.875
lighter_shade_factor = 0.92


# def generate_shade_array(item, side):
#     if side == 0:
#         side = "front"
#     else:
#         side = "back"
#     img = Image.open(f"templates/{item}_{side}.png")
#     img = img.convert("RGB")
#
#     d = img.getdata()
#     shade_array = []
#
#     # 0 - plain color, 1 - lighter shade, 2 - shade, 3 - outline
#     for item in d:
#
#         # change all white (also shades of whites)
#         if item[0] in list(range(240, 256)):
#             shade_array.append(0)
#         elif item[0] in list(range(220, 240)):
#             shade_array.append(1)
#         elif item[0] in list(range(45, 220)):
#             shade_array.append(2)
#         else:
#             shade_array.append(3)
#
#     shade_array = numpy.array(shade_array)
#     numpy.savez('templates/shades.npz', shade_array)


def change_print_shade(image, item):
    img = image.convert("RGB")

    d = img.getdata()
    new_image = []
    array = calculate_shades.arrs.get(item)
    for i in range(len(d)):
        if array[i] == 1:
            new_image.append((int(d[i][0] * lighter_shade_factor), int(d[i][1] * lighter_shade_factor),
                              int(d[i][2] * lighter_shade_factor)))
        elif array[i] == 2:
            new_image.append((int(d[i][0] * shade_factor), int(d[i][1] * shade_factor),
                              int(d[i][2] * shade_factor)))
        elif array[i] == 3:
            new_image.append((0, 0, 0))
        else:
            new_image.append(d[i])

    img.putdata(new_image)

    return img


# def calculate_outline(item):
#     img = cv2.imread(f"templates/{item.get(item)}")
#
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     mask = cv2.inRange(gray, 0, 50)
#
#     contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
#     mask[:] = 0
#     for con in contours:
#         mask = cv2.drawContours(mask, [con], -1, (255, 255, 255), -1)
#
#     img[mask != 255] = (255, 255, 255)
#     mask = Image.fromarray(mask)
#     mask.convert("RGB")
#     return mask


def paste(image, color, pos, item, side, angle, bg_deleted=False):
    color = tuple(color)

    if side == 0:
        item = item + "_front"
    else:
        item = item + "_back"
    template = Image.open(f"templates/{item}.png")
    mask = Image.open(f"templates/masks/mask_{item}.png")
    rgba_color = color + (255,)
    temporary_image = Image.new("RGBA", mask.size, rgba_color)

    # editing image
    if image is not None:
        if angle != 0:
            image = image.rotate(angle, expand=True)
        if bg_deleted:
            image = print_remove_bg(image)
        image = image.convert("RGBA")

        # pasting onto template
        if pos != "deleted":
            pos = tuple(pos)
            temporary_image.paste(image, pos, image)
    template.paste(temporary_image, (0, 0), mask)

    template = change_print_shade(template, item)
    return template


def image_to_bytes(template):
    bio = BytesIO()
    bio.name = "name.png"
    template.save(bio, "PNG")
    bio.seek(0)
    file = BufferedInputFile(bio.getvalue(), filename="name.png")
    return file


def image_to_json(image):
    return json.dumps(numpy.array(image).tolist())


def json_to_image(arr):
    return Image.fromarray(numpy.array(json.loads(arr), dtype='uint8'))


def print_remove_bg(myimage):
    # First Convert to Grayscale
    myimage.convert("RGB")
    myimage = numpy.asarray(myimage)
    myimage_grey = cv2.cvtColor(myimage, cv2.COLOR_RGB2GRAY)

    ret, baseline = cv2.threshold(myimage_grey, 127, 255, cv2.THRESH_TRUNC)

    ret, background = cv2.threshold(baseline, 126, 255, cv2.THRESH_BINARY)

    ret, foreground = cv2.threshold(baseline, 126, 255, cv2.THRESH_BINARY_INV)

    foreground = cv2.bitwise_and(myimage, myimage,
                                 mask=foreground)  # Update foreground with bitwise_and to extract real foreground

    # Convert black and white back into 3 channel greyscale
    background = cv2.cvtColor(background, cv2.COLOR_GRAY2RGB)

    # Combine the background and foreground to obtain our final image
    finalimage = background + foreground
    return Image.fromarray(finalimage)

# def print_remove_bg(image):
#     img = rembg.remove(image)
#     return img
