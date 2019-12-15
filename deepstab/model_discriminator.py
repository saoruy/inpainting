import torch
from torch import nn


class Discriminator(nn.Module):
    class Layer(nn.Module):
        def __init__(self, in_channels, out_channels, kernel_size=5, stride=2, padding=2, bn=True):
            super(Discriminator.Layer, self).__init__()
            self.conv = nn.utils.spectral_norm(
                nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, padding_mode='same')
            )
            if bn:
                self.bn = nn.BatchNorm2d(out_channels)
            else:
                self.bn = None
            self.activation = nn.LeakyReLU()

        def forward(self, x):
            x = self.conv(x)
            if self.bn:
                x = self.bn(x)
            x = self.activation(x)
            return x

    def __init__(self):
        super(Discriminator, self).__init__()

        self.model = nn.Sequential(
            Discriminator.Layer(3, 64, bn=False),
            Discriminator.Layer(64, 128),
            Discriminator.Layer(128, 256),
            Discriminator.Layer(256, 256),
            Discriminator.Layer(256, 256, bn=False)
        )

    def forward(self, x):
        return torch.sigmoid(torch.flatten(self.model(x), 1))