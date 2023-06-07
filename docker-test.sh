#!/bin/bash
set +ex

TAGS=("23.04")
USERNAME="ansibletest"
# PASSWORD=$(openssl passwd -1 <<< "ansibletestpass" | sed -e 's/[\/&]/\\&/g')
PASSWORD=$(echo "ansibletestpass" | openssl passwd -1 -stdin)

for TAG in "${TAGS[@]}"
do
docker build \
    --build-arg TAG=$TAG \
    --build-arg USERNAME=$USERNAME \
    --build-arg PASSWORD=$PASSWORD \
    -t ubuntu:$TAG \
    -f "tests/Dockerfile" \
    .

    docker run -it --rm -v $(pwd):/ansible --name ansible-ubuntu-$TAG ubuntu:$TAG
done

