# Copyright 2020 Google LLC
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
# docker build -t a-horse-with-no-neighs .
# docker run -it a-horse-with-no-neighs
# Default python3 is Python 3.8.10
FROM ubuntu:20.04 as chroot

RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*
RUN /usr/sbin/useradd --no-create-home -u 1000 user

COPY flag.txt /
COPY desert.py /home/user/

CMD ["/bin/python3", "/home/user/desert.py"]