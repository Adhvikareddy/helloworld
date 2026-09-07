# Q-SENTINEL RDP Container
# Provides a lightweight desktop for judge/operator access.
#
# Base image: lscr.io/linuxserver/webtop:ubuntu-xfce
# Source: https://docs.linuxserver.io/images/docker-webtop/
# Reason: Well-maintained, lightweight XFCE desktop with a built-in
#         web-based access layer on port 3000.  No native RDP needed;
#         the judge accesses the desktop through a browser.
#
# This container does NOT run any Q-SENTINEL core logic.
# It does NOT have access to the Docker socket.
# It does NOT run privileged.

# No custom Dockerfile needed — the image is used directly.
# This file exists for documentation purposes.
# The service is configured entirely in docker-compose.yml using the
# upstream image tag.
