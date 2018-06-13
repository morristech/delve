import delve
import logging
import torch
import torch.nn as nn

from delve import CheckLayerSat
from torch.autograd import Variable
from tqdm import tqdm, trange


class LayerCake(torch.nn.Module):
    def __init__(self, D_in, H1, H2, H3, H4, H5, D_out):
        """
        In the constructor we instantiate two nn.Linear modules and assign them as
        member variables.
        """
        super(LayerCake, self).__init__()
        self.linear1 = torch.nn.Linear(D_in, H1)
        self.linear2 = torch.nn.Linear(H1, H2)
        self.linear3 = torch.nn.Linear(H2, H3)
        self.linear4 = torch.nn.Linear(H3, H4)
        self.linear5 = torch.nn.Linear(H4, H5)
        self.linear6 = torch.nn.Linear(H5, D_out)

    def forward(self, x):
        """
        In the forward function we accept a Tensor of input data and we must return
        a Tensor of output data. We can use Modules defined in the constructor as
        well as arbitrary (differentiable) operations on Tensors.
        """
        x = self.linear1(x).clamp(min=0)
        x = self.linear2(x).clamp(min=0)
        x = self.linear3(x).clamp(min=0)
        x = self.linear4(x).clamp(min=0)
        x = self.linear5(x).clamp(min=0)
        y_pred = self.linear6(x)
        return y_pred

# N is batch size; D_in is input dimension;
# H is hidden dimension; D_out is output dimension.
N, D_in, D_out = 64, 100, 10

H1, H2, H3, H4, H5 = 100, 100, 100, 100, 100
# Create random Tensors to hold inputs and outputs
x = Variable(torch.randn(N, D_in))
y = Variable(torch.randn(N, D_out))

cuda = torch.cuda.is_available()
torch.manual_seed(1)

for h in [10, 100, 300]:

    # Create random Tensors to hold inputs and outputs
    x = Variable(torch.randn(N, D_in))
    y = Variable(torch.randn(N, D_out))

    model = LayerCake(D_in, h, H2, H3, H4, H5, D_out)

    if cuda:
        x, y, model = x.cuda(), y.cuda(), model.cuda()

    stats = CheckLayerSat('regression/h{}'.format(h), model)

    loss_fn = torch.nn.MSELoss(size_average=False)
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)
    steps_iter = trange(2000, desc='steps', leave=True, position=0)
    steps_iter.write("{:^80}".format("Regression - SixLayerNet - Hidden layer size {}".format(h)))
    for i in steps_iter:
        y_pred = model(x)
        loss = loss_fn(y_pred, y)
        steps_iter.set_description('loss=%g' % loss.data)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        stats.saturation()
    steps_iter.write('\n')
    stats.close()
    steps_iter.close()

