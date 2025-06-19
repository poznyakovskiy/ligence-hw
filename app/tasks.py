import os
import random
import uuid
from fastapi import File, UploadFile
from PIL import Image

from .database import get_db
from . import models

FS_PATH = "./fs/"
NUM_MODIFIED_IMAGES = 100
NUM_MODIFICATIONS_MIN = 100

def xor_swap(img: Image.Image, coord1: tuple, coord2: tuple) -> Image.Image:
    if img.mode not in ("L", "RGB", "RGBA"):
        raise ValueError("Only 'L', 'RGB', and 'RGBA' images are supported.")

    pixels = img.load()
    x1, y1 = coord1
    x2, y2 = coord2

    if img.mode == "L":
        # Grayscale: single channel byte
        a = pixels[x1, y1]
        b = pixels[x2, y2]

        a ^= b
        b ^= a
        a ^= b

        pixels[x1, y1] = a
        pixels[x2, y2] = b

    elif img.mode == "RGB" or img.mode == "RGBA":
        # apply XOR to each channel separately
        a = list(pixels[x1, y1])
        b = list(pixels[x2, y2])

        n_channels = 3 if img.mode == "RGB" else 4
        for i in range(n_channels):
            a[i] ^= b[i]
            b[i] ^= a[i]
            a[i] ^= b[i]

        pixels[x1, y1] = tuple(a)
        pixels[x2, y2] = tuple(b)

    return img

def add_image (file_bytes, filename):
    db = next(get_db())

    # Generate a unique filename with original extension
    ext = os.path.splitext(filename)[1]
    id = uuid.uuid4().hex
    path = f"{id}{ext}"
    save_path = os.path.join(FS_PATH, path)

    # Create directory for modified images
    modified_folder = os.path.join(FS_PATH, f"{id}")
    os.makedirs(modified_folder)

    # Open the image as PIL Image
    img = Image.open(file_bytes)
    width, height = img.size

    # Create NUM_MODIFIED_IMAGES modified images
    for modified_id in range(0, NUM_MODIFIED_IMAGES):
        modified_img = img.copy()
        modified_filename = f"{id}-{modified_id}{ext}"
        num_swaps = random.randint(NUM_MODIFICATIONS_MIN, width * height)
        swaps = []
        for _ in range(num_swaps):
            x0, y0 = random.randint(0, width - 1), random.randint(0, height - 1)
            x1, y1 = random.randint(0, width - 1), random.randint(0, height - 1)
            swaps.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1})
            modified_img = xor_swap(modified_img, (x0, y0), (x1, y1))
            
        modified_img.save(os.path.join(modified_folder, modified_filename))

        new_mod = models.Modification(
            image_id=id,
            id=modified_id,
            filename=modified_filename,
            modification_type="xor_swaps",
            params=swaps,
        )
        db.add(new_mod)

    # Add entry to Images table
    new_image = models.Image(id=id, filename=filename, path=path)
    db.add(new_image)
    db.commit()

    # Save the file
    img.save(save_path)

def check_mods():
    db = next(get_db())
    pending_mods = db.query(models.Modification).filter(models.Modification.verification.in_(["pending", "failed"])).all()

    num_successful = 0
    num_failed = 0

    for mod in pending_mods:
        try:
            # We only accept one modification for this assignment
            if mod.modification_type != "xor_swaps":
                raise ValueError(f"Unsupported modification type: {mod.modification_type}")

            # Load the modified image
            mod_path = os.path.join(FS_PATH, mod.image_id, mod.filename)
            if not os.path.exists(mod_path):
                raise FileNotFoundError(f"Modified image file not found: {mod_path}")
            img = Image.open(mod_path)

            reversed_params = list(reversed(mod.params))

            # Perform every modification step in reverse order
            for step in reversed_params:
                x0, y0 = step["x0"], step["y0"]
                x1, y1 = step["x1"], step["y1"]

                # The reverse of an XOR swap is the same as the original swap
                img = xor_swap(img, (x0, y0), (x1, y1))

            # Get the original image filename from Images table
            orig_image = db.query(models.Image).filter(models.Image.id == mod.image_id).first()
            if not orig_image:
                raise ValueError(f"Original image not found in DB for image_id: {mod.image_id}")

            orig_path = os.path.join(FS_PATH, orig_image.path)
            if not os.path.exists(orig_path):
                raise FileNotFoundError(f"Original image file not found: {orig_path}")

            orig_img = Image.open(orig_path)

            # Compare hashes of the reverted image and the original image
            orig_hash = hash(orig_img.tobytes())
            reverted_hash = hash(img.tobytes())
            if orig_hash == reverted_hash:
                mod.verification = "successful"
                num_successful += 1
            else:
                mod.verification = "failed"
                num_failed += 1
                db.add(mod)

        except Exception as e:
            print(f"Error processing modification {mod.id} for image {mod.image_id}: {e}")
            mod.verification = "failed"
            num_failed += 1
            db.add(mod)

    db.commit()