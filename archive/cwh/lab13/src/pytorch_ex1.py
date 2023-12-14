"""
PyTorch example 1: try to fit a given function with a naive neural network.
"""
import time
from typing import Tuple, Callable

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.utils.data
import tqdm

import models

torch.manual_seed(2023)

NUM_TRAIN_SAMPLES = 200

# use apple arm gpu
# device = torch.device("mps:0" if torch.backends.mps.is_available() else "cpu")
device = torch.device("cpu")


def default_target(x):
    """Actual function (ground truth)."""
    return x ** 2 + 2 * np.sin(x) + np.cos(x - 1) - 5


def custom_target1(x):
    return np.sin(5 * x + 2) + 0.05 * x ** 3 - 2 * x ** 2 + 3 * x - 1


class FuncDataset(torch.utils.data.Dataset):
    """Dataset for a given function."""

    def __init__(self,
                 target_func: Callable[[torch.Tensor], torch.Tensor],
                 x_span: Tuple[float, float],
                 num_samples: int = 200,
                 y_noise_std: float = 1.
                 ):
        super(FuncDataset, self).__init__()
        self._target = target_func
        self._length = num_samples
        self._x = torch.rand(size=(num_samples, 1)) * (x_span[1] - x_span[0]) + x_span[0]
        self._y = self._target(self._x) + torch.randn(size=(num_samples, 1)) * y_noise_std

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        return self._x[index], self._y[index]

    def get_all_data(self):
        return self._x.detach(), self._y.detach()


def main(epoch_count: int,
         lr: float,
         target_func=default_target,
         filename_prefix="custom",
         sample_count=200,
         batch_size=200,
         x_span=(-2, 2),
         save=False):
    """ Test the model with different hyperparameters. """
    model = models.Naive_NN().to(device)
    dataset_ = FuncDataset(target_func, x_span=x_span, num_samples=sample_count)
    dataloader = torch.utils.data.DataLoader(dataset_, batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # train
    start_time = time.time()
    model.train()
    epoch_loss_trace = []
    for epoch in tqdm.trange(epoch_count, desc=f"epoch_count={epoch_count}, lr={lr}"):
        this_epoch_loss = []
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            y_pred = model(x)
            loss = torch.nn.functional.mse_loss(y_pred, y)
            loss.backward()
            optimizer.step()
            this_epoch_loss.append(loss.item())
        epoch_loss_trace.append(np.mean(this_epoch_loss))

        # print(f"Epoch {epoch}: loss = {np.mean(avg_loss_trace)}")

    print(f"Training time: {time.time() - start_time}")

    # test
    model.eval()
    with torch.no_grad():
        x_test = torch.linspace(*x_span, 100).reshape(-1, 1)
        y_pred = model(x_test)
        y_true = target_func(x_test)
        mse = torch.nn.functional.mse_loss(y_pred, y_true)
        print(f"Test MSE: {mse}")

    # make the dots smaller
    plt.scatter(*(dataset_.get_all_data()),
                label="training data",
                color='b',
                s=1,
                alpha=0.4)

    plt.plot(x_test, y_pred, label="prediction", color='m', linewidth=2, alpha=0.8)
    plt.plot(x_test, y_true, label="ground truth", color='orange', linewidth=2, linestyle='--', alpha=1)

    plt.legend()

    # mark the hyperparams on the plot and save as the filename
    msg = f"epoch{epoch_count}_lr{lr}_bs{batch_size}"
    plt.title(msg)

    if save:
        plt.savefig(f"../output/ex1/{filename_prefix}_{msg}.svg")

    plt.show()

    # show the loss trace
    plt.semilogy(epoch_loss_trace)
    plt.title("loss trace")
    plt.show()


if __name__ == "__main__":
    # for epoch_count in [100, 1000, 10000, 50000]:
    #     for lr in [1, 1e-1, 1e-2, 1e-3]:
    #         # print(f"epoch_count={epoch_count}, lr={lr}")
    #         main(epoch_count=epoch_count,
    #              lr=lr,
    #              target_func=default_target,
    #              sample_count=NUM_TRAIN_SAMPLES,
    #              batch_size=200)

    main(epoch_count=200,
         lr=6e-3,
         target_func=custom_target1,
         filename_prefix="custom",
         sample_count=2048,
         batch_size=64,
         save=False)
