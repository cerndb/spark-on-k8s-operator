#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

FROM golang:1.10.2 as builder
ARG DEP_VERSION="0.4.1"
RUN apt-get update && \
    apt-get install -y bash git
ADD https://github.com/golang/dep/releases/download/v${DEP_VERSION}/dep-linux-amd64 /usr/bin/dep
RUN chmod +x /usr/bin/dep

WORKDIR ${GOPATH}/src/k8s.io/spark-on-k8s-operator
COPY Gopkg.toml Gopkg.lock ./
RUN dep ensure -vendor-only
COPY . ./
RUN go generate && \
    GOOS=linux GOARCH=amd64 go build -o /usr/bin/spark-operator && \
    chmod +x /usr/bin/spark-operator

FROM gitlab-registry.cern.ch/db/spark-service/docker-registry/spark-on-k8s:v2.3.0-xrootd-s3
COPY --from=builder /usr/bin/spark-operator /usr/bin/
ENTRYPOINT ["/usr/bin/spark-operator"]
