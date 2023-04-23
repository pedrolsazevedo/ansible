#!/bin/bash

# Define Gum style colors
GUM_YELLOW='\033[1;33m'
GUM_GREEN='\033[1;32m'
GUM_BLUE='\033[1;34m'
GUM_RESET='\033[0m'

declare -a packages=("python3" "ansible" "python3-pip" "ansible-lint")
declare -a install_packages=()

for package in "${packages[@]}"; do
    if ! command -v "$package" &> /dev/null; then
        install_packages+=("$package")
    fi
done

if [ ${#install_packages[@]} -eq 0 ]; then
    echo -e "${GUM_GREEN}All required packages are already installed.${GUM_RESET}"
else
    echo -e "${GUM_BLUE}Installing the following packages:${GUM_RESET} ${install_packages[@]}"
    sudo apt-get update
    for package in "${install_packages[@]}"; do
      if [ "$package" != "python3-pip" ] || [ ! -x "$(command -v pip)" ]
      then
          sudo apt-get install -y "$package"
      else
          echo -e "${GUM_YELLOW}Skipping installation of python3-pip since pip is already installed.${GUM_RESET}"
      fi
    done
fi

# Check and Create Ansible inventory and hosts file
if [ ! -d "/etc/ansible" ]; then
    echo -e "${GUM_BLUE}Ansible directory doesn't exists.${GUM_RESET}"
    sudo mkdir -p /etc/ansible
fi

if [ ! -f "/etc/ansible/hosts" ]; then
    echo -e "${GUM_BLUE}Ansible hosts doesn't exists.${GUM_RESET}"
    echo "[local]" | sudo tee -a /etc/ansible/hosts
    echo "localhost ansible_connection=local" | sudo tee -a /etc/ansible/hosts
else
    if ! grep -q "\[local\]" /etc/ansible/hosts || ! grep -q "localhost ansible_connection=local" /etc/ansible/hosts; then
        echo -e "${GUM_YELLOW}Updating Ansible hosts file.${GUM_RESET}"
        echo -e "\n[local]" | sudo tee -a /etc/ansible/hosts
        echo "localhost ansible_connection=local" | sudo tee -a /etc/ansible/hosts
    fi
fi

# Start basic configuration
echo -e "${GUM_BLUE}Starting Ansible configuration.${GUM_RESET}"
read -p "Install basic packages (vim, wget, Docker, Visual Studio Code, Google Chrome, Homebrew, TFENV (brew), Terraform and cz cli)? (y/n): " basic_config
if [[ $basic_config =~ ^[Yy]$ ]]; then
    ansible-playbook playbook.yml -K --extra-vars "current_user=$(logname)"
fi


# Validate if the user wants to install Azure tools (az cli, az copy, and azure storage explorer)
read -p "${GUM_BLUE}Install Azure tools (az cli, az copy and azure storage explorer)?${GUM_RESET} (y/n): " azure_tools
if [[ $azure_tools =~ ^[Yy]$ ]]; then
    ansible-playbook -K azure_tools.yml
fi

# Validade if want to install container extra (rancher-desktop and podman-desktop)
read -p "Install container extra(kubectl, rancher-desktop and podman-desktop)? (y/n): " container_extras
if [[ $container_extras =~ ^[Yy]$ ]]; then
    ansible-playbook -K container_extras.yml
fi


# SSH configuration
echo "Starting SSH configuration"
# Check if the user already has an SSH private key
# If no key or .ssh folder is found, the script will create the folder and the key
if [ ! -f ~/.ssh/id_rsa ]; then
    if [ ! -d ~/.ssh ]; then
        echo ".ssh folder doesn't exist, creation one."
        mkdir -p ~/.ssh
        chmod 700 ~/.ssh
    else
        echo ".ssh folder alteady exists" 
    fi
    echo "No key found, creating one:"
    ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
    echo "Your new public key is:"
    cat ~/.ssh/id_rsa.pub
else
    echo "Your public key is:"
    cat ~/.ssh/id_rsa.pub
fi

echo "Checking git configuration..."

echo "Checking git user name..."
if [[ -z "$(git config --global user.name)" ]]; then
    echo "Git user.name is not set"
    read -p "Enter your name: " name
    git config --global user.name "$name"
else
    echo "Git user name already configured"
fi

echo "Checking git email..."
if [[ -z "$(git config --global user.email)" ]]; then
    echo "Git user.email is not set"
    read -p "Enter your email: " email
    git config --global user.email "$email"
else
    echo "Git user email already configured"
fi
