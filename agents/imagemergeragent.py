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
        """
        Merge up to 5 images referenced in prompt using SAM + CLIP, refine with Stable Diffusion.

        Parameters:
            image_paths (List[str]): List of up to 5 image file paths
            prompt (str): Instruction referring to specific images by aliases + numbers
            output_path (str): Where to save the final image
            refine_prompt (str): Prompt for Stable Diffusion refinement
        """
        if len(image_paths) < 2:
            raise ValueError("At least 2 images are required.")
        if len(image_paths) > 5:
            raise ValueError("A maximum of 5 images is supported.")

        aliases = ["image", "photo", "picture"]
        prompt = prompt.lower()
        index_map = {}
        for i, path in enumerate(image_paths):
            for alias in aliases:
                index_map[f"{alias}{i+1}"] = path

        matches = re.findall(r"(image|photo|picture)\s?(\d)", prompt)
        selected = []
        for prefix, num in matches:
            key = f"{prefix}{num}"
            if key in index_map and index_map[key] not in selected:
                selected.append(index_map[key])
            if len(selected) == 2:
                break

        if len(selected) < 2:
            raise ValueError("Prompt must reference at least 2 distinct images by number (e.g. 'combine image1 and photo3').")

        image1 = Image.open(selected[0]).convert("RGB")
        image2 = Image.open(selected[1]).convert("RGB")

        size = (min(image1.width, image2.width), min(image1.height, image2.height))
        image1 = image1.resize(size)
        image2 = image2.resize(size)
        np1 = np.array(image1)
        np2 = np.array(image2)

        source_np, target_np = (np2, np1) if selected[0] in prompt else (np1, np2)
        print(f"[INFO] Merging '{selected[0]}' into '{selected[1]}'")

        mask = self._generate_mask(source_np, prompt)
        if mask is None:
            raise RuntimeError("No region found for prompt.")

        mask_3ch = cv2.merge([mask.astype(np.uint8) * 255] * 3)
        inv_mask = cv2.bitwise_not(mask_3ch)

        foreground = cv2.bitwise_and(source_np, mask_3ch)
        background = cv2.bitwise_and(target_np, inv_mask)
        merged_np = cv2.add(foreground, background)
        merged_pil = Image.fromarray(merged_np)

        print("[INFO] Refining with Stable Diffusion...")
        result = self._refine_with_diffusion(merged_pil, mask, refine_prompt)

        result.save(output_path)
        print(f"[INFO] Final output saved to {output_path}")
        return result


# A simple wrapper function to unify interface with other agents
def handle(message: str, context: str = "") -> str:
    """
    This handle function expects message to contain:
      - a list of local image file paths, separated by commas, on a line starting with "images:"
      - a prompt describing how to merge them

    Example message:
        images: path/to/img1.png, path/to/img2.png
        please combine image1 and photo2 seamlessly.

    Returns a text confirmation or error.
    """
    lines = message.strip().split("\n")
    image_paths = []
    prompt_lines = []

    for line in lines:
        if line.lower().startswith("images:"):
            paths_part = line[len("images:"):].strip()
            image_paths = [p.strip() for p in paths_part.split(",") if p.strip()]
        else:
            prompt_lines.append(line)

    prompt = " ".join(prompt_lines)
    if not image_paths:
        return "Error: No images specified. Please provide images in format 'images: path1, path2, ...'"

    try:
        agent = ImageMergeAgent()
        agent.merge_images(image_paths, prompt)
        return f"Images merged successfully and saved to merged_output.png"
    except Exception as e:
        return f"Error during image merge: {str(e)}"
