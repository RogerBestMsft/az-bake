Docker / Docker Desktop
=======================

Purpose
-------
Provide container runtime required for image building and local testing on Windows Dev Box.

Task Structure
--------------
This task uses the Azure Dev Box customization format:

```yaml
$schema: 1.0
tasks:
  - name: install-docker
    description: Install Docker Desktop for Windows
    parameters:
      command: winget
      packageId: Docker.DockerDesktop
      runAsUser: true
```

Verify
------
```bash
docker version
docker run --rm hello-world
```