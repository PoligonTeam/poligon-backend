"""
Copyright 2022 PoligonTeam

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from sanic import Blueprint
from sanic.exceptions import FileNotFound
from sanic.response import file

import os

cdn = Blueprint("cdn", "/cdn")

@cdn.get("/thumbnail/<file_name>")
async def get_thumbnail(request, file_name):
    if not file_name in os.listdir("./thumbnails"):
        raise FileNotFound("file not found", request.path, request.url)

    return await file("./thumbnails/" + file_name)

@cdn.get("/<file_name>")
async def get_file(request, file_name):
    if not file_name in os.listdir("./files"):
        raise FileNotFound("file not found", request.path, request.url)

    return await file("./files/" + file_name)