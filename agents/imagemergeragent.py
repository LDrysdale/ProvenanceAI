import os
from PIL import Image
import torch
from diffusers import StableDiffusionInpaintPipeline
import numpy as np
from io import BytesIO
import re

class ImageMergeAgent:
    def __init__(self, context=""):
        self.context = context
        self.pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting",
            torch_dtype=torch.float16
        ).to("cuda" if torch.cuda.is_available() else "cpu")

    def merge_images(self, prompt, image_paths):
        if not image_paths:
            return "No images provided for merging."

        # Size constraints
        MIN_SIZE = (256, 256)
        MAX_SIZE = (2048, 2048)

        images = []
        for path in image_paths:
            with Image.open(path) as img:
                if img.width < MIN_SIZE[0] or img.height < MIN_SIZE[1]:
                    return f"Image '{path}' is too small. Minimum size is {MIN_SIZE[0]}x{MIN_SIZE[1]}."
                if img.width > MAX_SIZE[0] or img.height > MAX_SIZE[1]:
                    return f"Image '{path}' is too large. Maximum size is {MAX_SIZE[0]}x{MAX_SIZE[1]}."
                images.append(img.convert("RGBA"))

        # Resize to largest common size
        max_width = max(img.width for img in images)
        max_height = max(img.height for img in images)
        target_size = (max_width, max_height)
        resized_images = [img.resize(target_size, Image.LANCZOS) for img in images]

        # Composite merge: take prompt suggestions to inform weights
        weights = self._parse_prompt_weights(prompt, len(resized_images))
        merged = Image.new("RGBA", target_size)
        for img, weight in zip(resized_images, weights):
            img_np = np.array(img).astype(np.float32) * weight
            if merged.getbbox():
                merged_np = np.array(merged).astype(np.float32)
                merged = Image.fromarray(np.clip(merged_np + img_np, 0, 255).astype(np.uint8))
            else:
                merged = Image.fromarray(np.clip(img_np, 0, 255).astype(np.uint8))

        refined = self._refine_with_diffusion(merged, prompt)
        output_path = "merged_output.png"
        refined.save(output_path, dpi=(300, 300))
        return f"Merged image saved as {output_path}"

    def _parse_prompt_weights(self, prompt, num_images):
        weights = [1.0 / num_images] * num_images  # default equal weight
        suggestions = re.findall(r"image\s*(\d+)\s*[:=]\s*(\d+(?:\.\d+)?)", prompt.lower())
        for idx_str, weight_str in suggestions:
            idx = int(idx_str) - 1
            if 0 <= idx < num_images:
                weights[idx] = float(weight_str)

        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]  # normalize
        return weights

    def _refine_with_diffusion(self, image_pil, prompt):
        TARGET_SIZE = (1024, 1024)
        image_pil = image_pil.resize(TARGET_SIZE)
        mask_pil = Image.new("L", TARGET_SIZE, 0)
        result = self.pipe(prompt=prompt, image=image_pil, mask_image=mask_pil).images[0]
        return result

def handle(message, context, image_paths):
    agent = ImageMergeAgent(context)
    return agent.merge_images(message, image_paths)
