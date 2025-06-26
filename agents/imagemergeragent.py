import torch
import clip
import cv2
import numpy as np
from PIL import Image
from segment_anything import sam_model_registry, SamPredictor
from diffusers import StableDiffusionInpaintPipeline
import re

class ImageMergeAgent:
    def __init__(self, sam_checkpoint_path="sam_vit_b.pth", model_type="vit_b", sd_model="runwayml/stable-diffusion-inpainting"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load CLIP
        self.model_clip, self.preprocess_clip = clip.load("ViT-B/32", device=self.device)

        # Load SAM
        print("[INFO] Loading SAM...")
        self.sam = sam_model_registry[model_type](checkpoint=sam_checkpoint_path)
        self.sam.to(self.device)
        self.predictor = SamPredictor(self.sam)

        # Load Stable Diffusion Inpainting model
        print("[INFO] Loading Stable Diffusion...")
        self.pipe = StableDiffusionInpaintPipeline.from_pretrained(
            sd_model,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        print("[INFO] All models ready.")

    def _clip_score(self, image_pil, prompt):
        image_input = self.preprocess_clip(image_pil).unsqueeze(0).to(self.device)
        text_input = clip.tokenize([prompt]).to(self.device)
        with torch.no_grad():
            image_features = self.model_clip.encode_image(image_input)
            text_features = self.model_clip.encode_text(text_input)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        return (image_features @ text_features.T).item()

    def _generate_mask(self, image_np, prompt, box_step=128):
        self.predictor.set_image(image_np)
        h, w = image_np.shape[:2]

        boxes = [
            [x, y, min(x + box_step, w), min(y + box_step, h)]
            for y in range(0, h, box_step)
            for x in range(0, w, box_step)
        ]
        boxes_tensor = torch.tensor(boxes, dtype=torch.float32).to(self.device)
        logits, masks, _ = self.predictor.predict_tensors(boxes=boxes_tensor, multimask_output=False)

        best_score, best_mask = -1, None
        for mask in masks:
            mask_np = mask[0].cpu().numpy() > 0.5
            if mask_np.sum() < 100:
                continue
            crop = Image.fromarray((image_np * mask_np[:, :, None]).astype(np.uint8))
            score = self._clip_score(crop, prompt)
            if score > best_score:
                best_score = score
                best_mask = mask_np

        return best_mask

    def _refine_with_diffusion(self, image_pil, mask_np, prompt="a seamless blend"):
        mask_pil = Image.fromarray((mask_np.astype(np.uint8) * 255)).convert("L")
        image_pil = image_pil.resize((512, 512))
        mask_pil = mask_pil.resize((512, 512))

        result = self.pipe(
            prompt=prompt,
            image=image_pil,
            mask_image=mask_pil,
        ).images[0]
        return result

    def merge_images(self, image_paths, prompt, output_path="merged_output.png", refine_prompt="a seamless blend"):
        if len(image_paths) < 2:
            raise ValueError("At least 2 images are required.")
        if len(image_paths) > 5:
            raise ValueError("A maximum of 5 images is supported.")

        aliases = ["image", "photo", "picture"]
        prompt_lower = prompt.lower()
        index_map = {}
        for i, path in enumerate(image_paths):
            for alias in aliases:
                index_map[f"{alias}{i+1}"] = path

        # Find all image references with positions in the prompt
        pattern = r"(image|photo|picture)\s?(\d)"
        matches = [(m.group(0), m.start()) for m in re.finditer(pattern, prompt_lower)]
        if len(matches) < 2:
            raise ValueError("Prompt must reference at least 2 distinct images by number (e.g. 'combine image1, photo2, and picture3').")
        if len(matches) > 5:
            matches = matches[:5]  # Limit to 5

        # Extract per-image prompt parts
        image_prompts = {}
        for i, (img_ref, start_pos) in enumerate(matches):
            end_pos = matches[i+1][1] if i+1 < len(matches) else len(prompt_lower)
            # Text after current img_ref up to next img_ref or end
            snippet = prompt_lower[start_pos + len(img_ref):end_pos].strip(" ,.-;:")
            image_prompts[img_ref] = snippet if snippet else "the main subject"

        # Open and resize all images to same size (min dimensions)
        selected_paths = [index_map[ref] for ref, _ in matches]
        images = [Image.open(p).convert("RGB") for p in selected_paths]
        min_width = min(img.width for img in images)
        min_height = min(img.height for img in images)
        size = (min_width, min_height)
        images = [img.resize(size) for img in images]
        images_np = [np.array(img) for img in images]

        # Start with first image as base canvas
        composite_np = images_np[0].copy()

        print("[INFO] Starting multi-image merging for images:", selected_paths)

        # For masks union used in diffusion refinement
        combined_mask = np.zeros((size[1], size[0]), dtype=bool)

        # Iterate over all images except first (already base)
        for i in range(1, len(images_np)):
            img_ref = matches[i][0]
            source_np = images_np[i]

            # Use the snippet associated with this image as mask prompt
            mask_prompt = f"{image_prompts.get(img_ref, '')} from {img_ref}"

            print(f"[INFO] Generating mask for {img_ref} with prompt: '{mask_prompt}'")
            mask = self._generate_mask(source_np, mask_prompt)
            if mask is None:
                print(f"[WARN] No mask found for {img_ref} with prompt '{mask_prompt}', skipping...")
                continue

            mask_3ch = cv2.merge([mask.astype(np.uint8) * 255] * 3)
            inv_mask = cv2.bitwise_not(mask_3ch)

            foreground = cv2.bitwise_and(source_np, mask_3ch)
            background = cv2.bitwise_and(composite_np, inv_mask)
            composite_np = cv2.add(foreground, background)

            combined_mask = combined_mask | mask

        composite_pil = Image.fromarray(composite_np)

        print("[INFO] Refining merged image with Stable Diffusion...")
        result = self._refine_with_diffusion(composite_pil, combined_mask.astype(np.uint8), refine_prompt)

        result.save(output_path)
        print(f"[INFO] Final output saved to {output_path}")
        return result


def handle(message: str, context: str = "", image_paths: list = None) -> str:
    """
    Handle image merge request.

    Args:
        message (str): Text prompt describing how to merge images.
        context (str): Optional context (unused here).
        image_paths (list): List of local image file paths.

    Returns:
        str: Success or error message.
    """
    if image_paths is None or len(image_paths) < 2:
        return "Error: Please upload at least two images to merge."

    try:
        agent = ImageMergeAgent()
        agent.merge_images(image_paths, message)
        return "Images merged successfully and saved to merged_output.png"
    except Exception as e:
        return f"Error during image merge: {str(e)}"
