# SJTU EE208

"""Train CIFAR-10 with PyTorch."""
import os

import torch
import torch.utils.data
import torchvision
import torchvision.transforms as transforms
import tqdm

from models import resnet20


def data_preprocess():
    # Data pre-processing
    print('==> Preparing data..')
    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(
            (0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(
            (0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    train_set = torchvision.datasets.CIFAR10(
        root='../data/', train=True, download=True, transform=transform_train)
    train_loader = torch.utils.data.DataLoader(
        train_set, batch_size=128, shuffle=True)

    test_set = torchvision.datasets.CIFAR10(
        root='../data/', train=False, download=True, transform=transform_test)
    test_loader = torch.utils.data.DataLoader(
        test_set, batch_size=128, shuffle=False)

    classes = ("airplane", "automobile", "bird", "cat",
               "deer", "dog", "frog", "horse", "ship", "truck")
    return train_loader, test_loader, classes


def get_model(use_pretrained=False):
    restore_model_path = '../checkpoint/pretrained/ckpt_4_acc_63.320000.pth'
    model = resnet20()
    if use_pretrained:
        model.load_state_dict(torch.load(restore_model_path)['net'])
    return model


def train(model, optimizer, criterion, train_loader, epoch: int):
    proc_bar = tqdm.tqdm(enumerate(train_loader), total=len(train_loader))
    model.train()
    train_loss = 0
    correct = 0
    total = 0
    for batch_idx, (x, y) in proc_bar:
        optimizer.zero_grad()
        y_hat = model(x)
        loss = criterion(y_hat, y)
        loss.backward()
        optimizer.step()
        # log batch count, loss, acc
        train_loss += loss.item()
        _, predicted = y_hat.max(1)
        total += y.size(0)
        correct += predicted.eq(y).sum().item()

        # print('Epoch [%d] Batch [%d/%d] Loss: %.3f | Training Acc: %.3f%% (%d/%d)'
        #       % (epoch, batch_idx + 1, len(train_loader), train_loss / (batch_idx + 1),
        #          100. * correct / total, correct, total))

        # msg contains batch count, loss, acc
        msg = f"Epoch [{epoch}] Batch [{batch_idx + 1}/{len(train_loader)}] Loss: {train_loss / (batch_idx + 1):.3f} | Training Acc: {100. * correct / total:.3f}% ({correct}/{total})"

        proc_bar.set_description(msg)


def test(model, criterion, test_loader, epoch: int, save=True):
    model.eval()
    test_loss = 0
    correct = 0
    total = 0
    with torch.no_grad():
        # count correct predictions
        for x, y in tqdm.tqdm(test_loader, desc=f"Epoch [{epoch}] Testing"):
            y_hat = model(x)
            test_loss += criterion(y_hat, y).item()
            _, predicted = torch.max(y_hat.data, 1)
            correct += predicted.eq(y.data).sum().item()
            total += y.size(0)

    accuracy = 100. * correct / total
    print(f'Epoch: {epoch}\tTest Loss: {test_loss:.6f}\tTest Accuracy: {accuracy:.3f}%')

    if not save:
        return

    # save checkpoint
    state = {
        'net': model.state_dict(),
        'acc': accuracy,
        'epoch': epoch,
    }
    if not os.path.isdir('../checkpoint'):
        os.mkdir('../checkpoint')
    torch.save(state, f'../checkpoint/ckpt_{epoch}_acc_{accuracy}.pth')
    print(f'Checkpoint saved as {f"../checkpoint/ckpt_{epoch}_acc_{accuracy}.pth"}')


def main(
        use_pretrained=False,
):
    epoch_lr = [(5, 0.01)] if use_pretrained else [(5, 0.1), (5, 0.01)]
    train_loader, test_loader, classes = data_preprocess()
    model = get_model(use_pretrained)
    criterion = torch.nn.CrossEntropyLoss()

    cur_epoch = 0
    for epoch_count, lr in epoch_lr:
        optimizer = torch.optim.SGD(model.parameters(), lr=lr, weight_decay=5e-4)
        for epoch in range(cur_epoch, cur_epoch + epoch_count):
            train(model, optimizer, criterion, train_loader, epoch)
            test(model, criterion, test_loader, epoch)

        cur_epoch += epoch_count


def just_test(checkpoint_dir):
    train_loader, test_loader, classes = data_preprocess()
    model = resnet20()
    model.load_state_dict(torch.load(checkpoint_dir)['net'])
    criterion = torch.nn.CrossEntropyLoss()
    test(model, criterion, test_loader, 0, save=False)


if __name__ == '__main__':
    # main(use_pretrained=True)
    just_test("../checkpoint/ckpt_9_acc_73.54.pth")
