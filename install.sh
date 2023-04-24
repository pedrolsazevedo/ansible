#!/bin/bash

# Define Gum style colors
gum_style_defition(){
    GUM_YELLOW='\033[1;33m'
    GUM_GREEN='\033[1;32m'
    GUM_BLUE='\033[1;34m'
    GUM_RESET='\033[0m'
}


check_requirements() {
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
}

ansible_configuration() {
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
}

run_playbooks() {
    playbooks=(
        "basic_setup.yml|Installs basic packages (vim, wget, Docker, Visual Studio Code, Google Chrome, Homebrew, TFENV (brew), Terraform, NVM and cz cli)."
        "azure_tools.yml|Installs Azure tools (az cli, az copy and azure storage explorer)"
        "container_extras.yml|Installs container extras (kubectl, rancher-desktop, and podman-desktop)"
    )

    selected_playbooks=()

    for playbook in "${playbooks[@]}"
    do
        name=$(echo "$playbook" | cut -d "|" -f 1)
        desc=$(echo "$playbook" | cut -d "|" -f 2)
        
        read -p "Do you want to run the playbook \"$name\"? ($desc) [yY/n]" choice

        if [[ "$choice" =~ ^[Yy]$ ]]; then
            selected_playbooks+=("$name")
        fi
    done

    if [ ${#selected_playbooks[@]} -eq 0 ]; then
        echo -e "${GUM_YELLOW}No playbooks selected. 😞${GUM_RESET}"
        return 0
    fi

    for playbook in "${selected_playbooks[@]}"
    do
        echo -e "${GUM_GREEN}Running playbook \"$playbook\"... 🚀${GUM_RESET}"
        ansible-playbook "playbooks/$playbook" -K --extra-vars "current_user=$(logname)"
    done
}

git_configuration() {
    echo -e "${GUM_GREEN}🔑 Starting SSH configuration${GUM_RESET}"
    # Check if the user already has an SSH private key
    # If no key or .ssh folder is found, the script will create the folder and the key
    if [ ! -f ~/.ssh/id_rsa ]; then
        if [ ! -d ~/.ssh ]; then
            echo "📁 .ssh folder doesn't exist, creating one."
            mkdir -p ~/.ssh
            chmod 700 ~/.ssh
        else
            echo "📁 .ssh folder already exists" 
        fi

        echo -e "🔑 No key found, creating one:"
        ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
        echo -e "🔑 Your new public key is:"
        cat ~/.ssh/id_rsa.pub
    else
        echo -e "🔑${GUM_GREEN} Your public key is:${GUM_RESET}"
        echo -e "${GUM_YELLOW} $(cat ~/.ssh/id_rsa.pub) ${GUM_RESET}"
    fi

    echo -e "🔍 Checking Git configuration..."

    echo -e "${GUM_GREEN}👤 Checking Git user name...${GUM_RESET}"
    if [[ -z "$(git config --global user.name)" ]]; then
        echo -e "${GUM_YELLOW}👤 Git user.name is not set${GUM_RESET}"
        read -p "Enter your name: " name
        git config --global user.name "$name"
    else
        echo -e "${GUM_GREEN}👤 Git user name already configured${GUM_RESET}"
    fi

    echo -e "${GUM_GREEN}✉️  Checking Git email..."
    if [[ -z "$(git config --global user.email)" ]]; then
        echo -e"${GUM_YELLOW}✉️  Git user.email is not set"
        read -p "Enter your email: " email
        git config --global user.email "$email"
    else
        echo -e "${GUM_GREEN}✉️  Git user email already configured${GUM_RESET}"
    fi

    echo -e "${GUM_GREEN}✅ Git and SSH configuration complete${GUM_RESET}"
}


gum_style_defition
check_requirements
ansible_configuration
run_playbooks
git_configuration
