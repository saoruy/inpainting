import glob
import os

import torch
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data.dataloader import DataLoader
from torchvision.transforms.functional import to_pil_image

from inpainting.external.models import DeepFillV1Model, FlowNet2Model, LiteFlowNetModel
from inpainting.algorithm import FlowAndFillInpaintingAlgorithm, FillInpaintingAlgorithm, FlowInpaintingAlgorithm
from inpainting.load import VideoDataset, DynamicMaskVideoDataset
from inpainting.visualize import animate_sequence
from scripts.train import InpaintingModel

batch_size = 1
size = (256, 256)

frame_dataset = VideoDataset(
    list(glob.glob('data/raw/video/DAVIS/JPEGImages/480p/flamingo')),
    frame_type='image',
    transform=transforms.Compose([
        transforms.Resize(size, interpolation=Image.BILINEAR),
        transforms.ToTensor()
    ]))
mask_dataset = VideoDataset(
    list(glob.glob('data/processed/video/DAVIS/Annotations_dilated/480p/flamingo')),
    frame_type='mask',
    transform=transforms.Compose([
        transforms.Resize(size, interpolation=Image.NEAREST),
        transforms.ToTensor()
    ]))
dataset = DynamicMaskVideoDataset(frame_dataset, mask_dataset)
# mask_dataset = RectangleMaskDataset(
#     size[1], size[0],
#     (128 - 16, 128 - 16, 32, 32),
#     # '../data/raw/mask/demo',
#     # '../data/raw/mask/qd_imd/test',
#     transform=transform)
# dataset = StaticMaskVideoDataset(frame_dataset, mask_dataset)

data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

with torch.no_grad():
    flow_model = LiteFlowNetModel().cuda().eval()
    # inpainting_algorithm = FlowInpaintingAlgorithm(flownet2)

    fill_model = DeepFillV1Model().cuda().eval()
    # inpainting_algorithm = FillInpaintingAlgorithm(deepfillv1)

    inpainting_algorithm = FlowAndFillInpaintingAlgorithm(flow_model, fill_model)

    for sample in iter(data_loader):
        frames, masks, _ = sample
        frames = list(map(lambda x: x.cuda(), frames))
        masks = list(map(lambda x: x.cuda(), masks))
        inpainting_algorithm.reset()
        frames_filled, masks_filled = inpainting_algorithm.inpaint(frames, masks)
        frames_filled = list(map(lambda x: x.cpu(), frames_filled))
        masks_filled = list(map(lambda x: x.cpu(), masks_filled))

        frames = list(map(lambda x: x.cpu(), frames))
        masks = list(map(lambda x: x.cpu(), masks))
        target_directory = 'results'
        os.makedirs(target_directory, exist_ok=True)
        for i in range(batch_size):
            animate_sequence(
                [to_pil_image(f[i], mode='RGB') for f in frames],
                # [to_pil_image(m[i], mode='L') for m in masks],
                [to_pil_image(f[i], mode='RGB') for f in frames_filled],
                # [to_pil_image(m[i], mode='L') for m in masks_filled]
            ).save(f'{target_directory}/sequence.mp4', fps=24, dpi=300)
