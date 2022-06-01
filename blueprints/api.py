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
from sanic.exceptions import FileNotFound, InvalidUsage, Unauthorized, HeaderNotFound
from sanic.response import json
from sanic.views import HTTPMethodView

from datetime import datetime
from PIL import Image
from urllib.parse import unquote

from models import Account, Upload
from config import FILE_EXTENSIONS, FILE_EXTENSIONS_WITH_EMBED, FILE_EXTENSIONS_WITH_THUMBNAIL
from utils import encode_text, decode_text

import os, time, random, re, string, hashlib

api = Blueprint("api", url_prefix="/api")

class TextParser:
    def __init__(self, username, file_name, size: int, timestamp: float):
        self.username = username
        self.file_name = file_name
        self.size = TextParser.humanize_size(size)
        self.timestamp = timestamp

    def put_variables(self, text):
        text = text.replace(r"%username", self.username)
        text = text.replace(r"%filename", self.file_name)
        text = text.replace(r"%size", self.size)
        text = datetime.utcfromtimestamp(self.timestamp + 60 * 60 * 2).strftime(text)

        return text

    @classmethod
    def humanize_size(cls, size: int):
        humanized_size = None

        for unit in ("", "k", "M"):
            if not size >= 1000:
                humanized_size = "%.2f %sB" % (size, unit)
                break

            size /= 1000

        return humanized_size

class File(HTTPMethodView):
    async def get(self, request, file_name):
        file_name = unquote(file_name)

        if "\u200f" in file_name:
            file_name = decode_text(file_name)

        upload = await Upload.filter(filename=file_name).first()

        if not upload:
            raise FileNotFound("file not found", request.path, request.url)

        file_extension = upload.filename.split(".", 1)[-1]

        data = dict(upload)
        del data["deletion_secret"]

        data["embed"] = False

        if file_extension in ("png", "jpg", "jpeg", "gif"):
            data["type"] = "image"
        elif file_extension in ("mp3", "m4a"):
            data["type"] = "audio"
        elif file_extension in ("mp4", "mov", "webm"):
            data["type"] = "video"

        if file_extension in FILE_EXTENSIONS_WITH_EMBED and (upload.title or upload.description or upload.site_name or upload.color):
            data["embed"] = True

        return json(data)

    async def delete(self, request, file_name):
        if not request.json or not "deletion_secret" in request.json:
            raise InvalidUsage("missing secret")

        deletion_secret = request.json.get("deletion_secret")

        file = await Upload.filter(filename = file_name, deletion_secret = deletion_secret).first()

        if not file:
            raise Unauthorized("invalid deletion secret")

        await file.delete()

        os.remove("./files/" + file_name)

        return json({"message": "file deleted"}, 204)

@api.post("/upload")
async def upload(request):
    if not ("content-type" in request.headers and "multipart/form-data" in request.headers["content-type"]):
        raise HeaderNotFound("missing content-type header")

    if not "file" in request.files:
        raise InvalidUsage("missing file")

    if not "authorization" in request.headers:
        raise HeaderNotFound("missing authorization header")

    account = await Account.filter(token = request.headers.get("authorization")).first()

    if not account:
        raise Unauthorized("invalid authorization")

    timestamp = time.time()

    file = request.files.get("file")
    file_extension = file.name.split(".", 1)[-1]

    if not file_extension in FILE_EXTENSIONS:
        raise InvalidUsage("invalid file type")

    file_name = "".join(random.choice(string.ascii_letters) for _ in range(10)) + "." + file_extension

    while file_name in os.listdir("./files"):
        file_name = "".join(random.choice(string.ascii_letters) for _ in range(10)) + "." + file_extension

    deletion_secret = hashlib.sha512((str(timestamp) + request.headers["authorization"] + request.headers.get("user-agent", "Mozilla/5.0 (Web0S; Linux/SmartTV) AppleWebKit/537.36 (KHTML, like Gecko) QtWebEngine/5.2.1 Chrome/38.0.2125.122 Safari/537.36 LG Browser/8.00.00(LGE; 60UH6550-UB; 03.00.15; 1; DTV_W16N); webOS.TV-2016; LG NetCast.TV-2013 Compatible (LGE, 60UH6550-UB, wireless)")).encode()).hexdigest()
    size = len(file.body)

    upload = await Upload.create(id=account.id, username=account.username, filename=file_name, deletion_secret=deletion_secret, timestamp=timestamp, size=size)

    with open("./files/" + file_name, "wb") as f:
        f.write(file.body)

    if file_extension in FILE_EXTENSIONS_WITH_THUMBNAIL:
        image = Image.open("./files/" + file_name)
        image.thumbnail((512, 512), Image.ANTIALIAS)
        image.save("./thumbnails/" + file_name.split(".", 1)[0] + ".png", format="png")

    if file_extension in FILE_EXTENSIONS_WITH_EMBED:
        parser = TextParser(account.username, file_name, size, timestamp)

        for key, values in request.form.items():
            value = values[0]

            if key == "title":
                upload.title = parser.put_variables(value)

            elif key == "description":
                upload.description = parser.put_variables(value)

            elif key == "site_name":
                upload.site_name = parser.put_variables(value)

            elif key == "color":
                match = re.match(r"[a-fA-F0-9]+", value)

                if match and match.span == (0, 6):
                    upload.color = int(value, 16)

                if value == "random":
                    upload.color = random.randint(0, 0xffffff)

            elif key == "invisible_url":
                file_name = encode_text(file_name)

    await upload.save()

    return json({"filename": file_name, "deletion_secret": deletion_secret})

api.add_route(File.as_view(), "/file/<file_name>")
