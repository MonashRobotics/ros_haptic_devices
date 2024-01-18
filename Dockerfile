# Generated using roboco version 0.0.4
FROM ros:noetic

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    udev \
    ros-$ROS_DISTRO-joint-state-publisher \
    ros-$ROS_DISTRO-joint-state-publisher-gui \
    ros-$ROS_DISTRO-robot-state-publisher \
    ros-$ROS_DISTRO-rviz \
    && rm -rf /var/lib/apt/lists/*

# Add non-root user
ENV USERNAME=roboco
ENV USER_UID=1000
ENV USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

RUN usermod -aG dialout $USERNAME

# Install geomagic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    freeglut3-dev  \
    g++ \
    libdrm-dev \
    libexpat1-dev \
    libglw1-mesa \
    libglw1-mesa-dev \
    libmotif-dev \
    libncurses5-dev \
    libncurses5\
    libraw1394-dev \
    libx11-dev \
    libxdamage-dev \
    libxext-dev \
    libxt-dev \
    libxxf86vm-dev \
    tcsh \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and enter a ros workspace
WORKDIR /home/${USERNAME}/ros_ws
RUN mkdir -p /home/${USERNAME}/ros_ws/src

# Install python dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

#install touchx drivers
COPY ./device_drivers /home/${USERNAME}/device_drivers

RUN /bin/bash -c 'cd /home/${USERNAME} && echo "y" | ./device_drivers/open_haptics_install.sh'

RUN /bin/bash -c 'cd /home/${USERNAME} && echo "y" | ./device_drivers/touch_driver_install_2022.sh'

# Change to the non-root user and update file ownership
RUN chown -R ${USERNAME} /home/${USERNAME}
USER $USERNAME
# Change prompt to show we are in a docker container
RUN echo "export PS1='\[\e]0;\u@docker: \w\a\]${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@docker\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '" >> /home/${USERNAME}/.bashrc
# Automatically source ros setup files
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/${USERNAME}/.bashrc

# Build source packages
RUN /bin/bash -c '. /opt/ros/$ROS_DISTRO/setup.bash; cd /home/${USERNAME}/ros_ws; catkin_make'