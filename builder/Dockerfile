# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

FROM mcr.microsoft.com/azure-cli:latest
WORKDIR /

ARG IMAGE_VERSION
ARG REPO_URL=https://github.com/rogerbestmsft/az-bake

# Metadata as defined at http://label-schema.org
ARG BUILD_DATE

ENV AZ_BAKE_IMAGE_BUILDER=1
ENV AZ_BAKE_IMAGE_BUILDER_VERSION=$IMAGE_VERSION

LABEL maintainer="Microsoft" \
    org.opencontainers.image.created=$BUILD_DATE \
    org.opencontainers.image.url="$REPO_URL" \
    org.opencontainers.image.source="$REPO_URL" \
    org.opencontainers.image.version=$IMAGE_VERSION \
    org.opencontainers.image.vendor="Microsoft" \
    org.opencontainers.image.title="Bake Image Builder" \
    org.opencontainers.image.description="The Bake Image Builder is used to build images using packer." \
    org.opencontainers.image.documentation="$REPO_URL/tree/main/builder" \
    org.opencontainers.image.licenses="MIT" \
    org.label-schema.schema-version="1.0" \
    org.label-schema.vendor="Microsoft" \
    org.label-schema.name="Bake Image Builder" \
    org.label-schema.version=$IMAGE_VERSION \
    org.label-schema.license="MIT" \
    org.label-schema.description="The Bake Image Builder is used to build images using packer." \
    org.label-schema.url="$REPO_URL" \
    org.label-schema.usage="$REPO_URL/tree/main/builder" \
    org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.vcs-url="$REPO_URL.git" \
    org.label-schema.docker.cmd="docker run ghcr.io/rogerbestmsft/az-bake/builder:$IMAGE_VERSION"

# install packer
RUN tdnf install -y packer

# install az-bake
RUN az extension add --source ${REPO_URL}/releases/download/v${IMAGE_VERSION}/bake-${IMAGE_VERSION}-py3-none-any.whl -y

# Terminate container on stop
STOPSIGNAL SIGTERM

CMD [ "" ]
ENTRYPOINT ["az", "bake", "_builder", "build", "--verbose"]