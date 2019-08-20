import torch
import torch.nn as nn


class Lovasz(nn.Module):
    """Lovasz Loss. Cf: https://arxiv.org/abs/1705.08790 """

    def __init__(self):
        super().__init__()

    def forward(self, inputs, targets):

        N, C, H, W = inputs.size()
        #masks = torch.zeros(N, C, H, W).to(targets.device).scatter_(1, targets.view(N, 1, H, W), 1)
        masks = targets

        loss = 0.0

        for mask, input in zip(masks.view(N, -1), inputs.view(N, -1)):
            
            input = input.double() 
            max_margin_errors = 1.0 - ((mask * 2 - 1) * input)
            errors_sorted, indices = torch.sort(max_margin_errors, descending=True)
            labels_sorted = mask[indices.data]

            inter = labels_sorted.sum() - labels_sorted.cumsum(0)
            union = labels_sorted.sum() + (1.0 - labels_sorted).cumsum(0)
            iou = 1.0 - inter / union

            p = len(labels_sorted)
            if p > 1:
                iou[1:p] = iou[1:p] - iou[0:-1]

            loss += torch.dot(nn.functional.relu(errors_sorted), iou)

        return loss / N
