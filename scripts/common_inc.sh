#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPTNAME="$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"

if [[ $EUID -eq 0 ]]; then
  echo "Error: ${SCRIPTNAME} must not be excecuted by root"
  exit 1
fi

OWNER="${TRAVIS_REPO_SLUG%/*}"
GLBACKEND_GIT_REPO="https://github.com/$OWNER/GLBackend.git"
GLCLIENT_GIT_REPO="https://github.com/$OWNER/GLClient.git"

REPO_DIR='/data/deb'

if test ${GLOBALEAKS_BUILD_ENV}; then
  BUILD_DIR=${GLOBALEAKS_BUILD_ENV}
  mkdir -p ${BUILD_DIR}
else
  BUILD_DIR=$( readlink -m ${DIR}/../../)
fi

cd ${BUILD_DIR}

GLBACKEND_DIR=$( readlink -m ${BUILD_DIR}/GLBackend)
GLCLIENT_DIR=$( readlink -m ${BUILD_DIR}/GLClient)
GLBACKEND_TMP=${GLBACKEND_DIR}_tmp
GLCLIENT_TMP=${GLCLIENT_DIR}_tmp
GLB_BUILD=$( readlink -m ${GLBACKEND_TMP}/glbackend_build)
GLC_BUILD=$( readlink -m ${GLCLIENT_TMP}/glclient_build)

echo "Running command ${SCRIPTNAME} $*"
echo "Build directory used: ${BUILD_DIR}"
echo "To override this do: 'GLOBALEAKS_BUILD_ENV=/what/you/want && export GLOBALEAKS_BUILD_ENV'"

echo "[+] Setupping GLClient and GLBackend build environments"
