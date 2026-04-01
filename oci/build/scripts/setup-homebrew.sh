#!/bin/bash
set -e

useradd -m -s /bin/bash linuxbrew && echo 'linuxbrew ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

su - linuxbrew -c 'NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
su - linuxbrew -c '/home/linuxbrew/.linuxbrew/bin/brew install helm kubectl k9s mise kubelogin'
su - linuxbrew -c '/home/linuxbrew/.linuxbrew/bin/mise use -g -y terraform@latest terragrunt@latest'

echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /home/linuxbrew/.bashrc
echo 'eval "$(mise activate bash)"' >> /home/linuxbrew/.bashrc
