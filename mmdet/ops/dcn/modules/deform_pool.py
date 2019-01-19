from torch import nn

from ..functions.deform_pool import deform_roi_pooling


class DeformRoIPooling(nn.Module):

    def __init__(self,
                 spatial_scale,
                 out_size,
                 output_dim,
                 no_trans,
                 group_size=1,
                 part_size=None,
                 sample_per_part=4,
                 trans_std=.0):
        super(DeformRoIPooling, self).__init__()
        self.spatial_scale = spatial_scale
        self.out_size = out_size
        self.output_dim = output_dim
        self.no_trans = no_trans
        self.group_size = group_size
        self.part_size = out_size if part_size is None else part_size
        self.sample_per_part = sample_per_part
        self.trans_std = trans_std

    def forward(self, data, rois, offset):
        if self.no_trans:
            offset = data.new()
        return deform_roi_pooling(
            data, rois, offset, self.spatial_scale, self.out_size,
            self.output_dim, self.no_trans, self.group_size, self.part_size,
            self.sample_per_part, self.trans_std)


class ModulatedDeformRoIPoolingPack(DeformRoIPooling):

    def __init__(self,
                 spatial_scale,
                 out_size,
                 output_dim,
                 no_trans,
                 group_size=1,
                 part_size=None,
                 sample_per_part=4,
                 trans_std=.0,
                 deform_fc_dim=1024):
        super(ModulatedDeformRoIPoolingPack, self).__init__(
            spatial_scale, out_size, output_dim, no_trans, group_size,
            part_size, sample_per_part, trans_std)

        self.deform_fc_dim = deform_fc_dim

        if not no_trans:
            self.offset_fc = nn.Sequential(
                nn.Linear(
                    self.out_size * self.out_size * self.output_dim,
                    self.deform_fc_dim), nn.ReLU(inplace=True),
                nn.Linear(self.deform_fc_dim, self.deform_fc_dim),
                nn.ReLU(inplace=True),
                nn.Linear(self.deform_fc_dim,
                          self.out_size * self.out_size * 2))
            self.offset_fc[4].weight.data.zero_()
            self.offset_fc[4].bias.data.zero_()
            self.mask_fc = nn.Sequential(
                nn.Linear(
                    self.out_size * self.out_size * self.output_dim,
                    self.deform_fc_dim), nn.ReLU(inplace=True),
                nn.Linear(self.deform_fc_dim,
                          self.out_size * self.out_size * 1),
                nn.Sigmoid())
            self.mask_fc[2].weight.data.zero_()
            self.mask_fc[2].bias.data.zero_()

    def forward(self, data, rois):
        if self.no_trans:
            offset = data.new()
        else:
            n = rois.shape[0]
            offset = data.new()
            x = deform_roi_pooling(data, rois, offset, self.spatial_scale,
                                   self.out_size, self.output_dim, True,
                                   self.group_size, self.part_size,
                                   self.sample_per_part, self.trans_std)
            offset = self.offset_fc(x.view(n, -1))
            offset = offset.view(n, 2, self.out_size, self.out_size)
            mask = self.mask_fc(x.view(n, -1))
            mask = mask.view(n, 1, self.out_size, self.out_size)
            feat = deform_roi_pooling(
                data, rois, offset, self.spatial_scale, self.out_size,
                self.output_dim, self.no_trans, self.group_size,
                self.part_size, self.sample_per_part, self.trans_std) * mask
            return feat
        return deform_roi_pooling(
            data, rois, offset, self.spatial_scale, self.out_size,
            self.output_dim, self.no_trans, self.group_size, self.part_size,
            self.sample_per_part, self.trans_std)


class DeformRoIPoolingPack(DeformRoIPooling):

    def __init__(self,
                 spatial_scale,
                 out_size,
                 output_dim,
                 no_trans,
                 group_size=1,
                 part_size=None,
                 sample_per_part=4,
                 trans_std=.0,
                 deform_fc_dim=1024):
        super(DeformRoIPoolingPack, self).__init__(
            spatial_scale, out_size, output_dim, no_trans, group_size,
            part_size, sample_per_part, trans_std)

        self.deform_fc_dim = deform_fc_dim

        if not no_trans:
            self.offset_fc = nn.Sequential(
                nn.Linear(
                    self.out_size * self.out_size * self.output_dim,
                    self.deform_fc_dim), nn.ReLU(inplace=True),
                nn.Linear(self.deform_fc_dim, self.deform_fc_dim),
                nn.ReLU(inplace=True),
                nn.Linear(self.deform_fc_dim,
                          self.out_size * self.out_size * 2))
            self.offset_fc[4].weight.data.zero_()
            self.offset_fc[4].bias.data.zero_()

    def forward(self, data, rois):
        if self.no_trans:
            offset = data.new()
        else:
            n = rois.shape[0]
            offset = data.new()
            x = deform_roi_pooling(data, rois, offset, self.spatial_scale,
                                   self.out_size, self.output_dim, True,
                                   self.group_size, self.part_size,
                                   self.sample_per_part, self.trans_std)
            offset = self.offset_fc(x.view(n, -1))
            offset = offset.view(n, 2, self.out_size, self.out_size)
            feat = deform_roi_pooling(
                data, rois, offset, self.spatial_scale, self.out_size,
                self.output_dim, self.no_trans, self.group_size,
                self.part_size, self.sample_per_part, self.trans_std)
            return feat
        return deform_roi_pooling(
            data, rois, offset, self.spatial_scale, self.out_size,
            self.output_dim, self.no_trans, self.group_size, self.part_size,
            self.sample_per_part, self.trans_std)
