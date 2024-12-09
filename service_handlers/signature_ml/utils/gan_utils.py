import os
from PIL import Image

def make_square(image, min_size=512, fill_color=(0, 0, 0)):
    '''
        Scale the image to occupy the full width, and pad top and bottom to make it square.
    '''
    x, y = image.size
    size = max(min_size, x)
    # Scale image to fill the width
    new_width = size
    new_height = int(y * (size / x))
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    # Create new square image
    new_im = Image.new('RGB', (size, size), fill_color)
    # Paste the image onto the center vertically
    top_padding = int((size - new_height) / 2)
    new_im.paste(image, (0, top_padding))
    new_im = new_im.resize((512, 512))
    return new_im


def resize_images(path):
    '''
        Resize all the images present in path that matches the ips used in cyclegan
        training
    '''
    dirs = os.listdir(path)
    for item in dirs:
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            image = Image.open(item_path)
            image = make_square(image)
            image = image.convert('L')
            image.save(item_path)
            print(f"\n Rezied image: {item_path}")
        else:
            print(f"\n Cannot resize file. {item_path} not found.")

# test_path = 'runs/detect/exp/crops/DLSignature/'
# resize_images(test_path)