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

from tortoise import Model
from tortoise.fields import CharField, FloatField, IntField, TextField, JSONField

class Upload(Model):
    user_id = TextField()
    username = TextField()
    filename = CharField(max_length=16, pk=True)
    deletion_secret = TextField()
    timestamp = FloatField()
    size = IntField()
    title = TextField()
    description = TextField()
    site_name = TextField()
    color = IntField()

    class Meta:
        table = "uploads"

class Account(Model):
    id = CharField(max_length=16, pk=True)
    username = TextField()
    token = TextField()
    password = JSONField()
    salt = JSONField()
    permissions = IntField()
    discord_id = TextField()
    discord_access_token = TextField()
    discord_refresh_token = TextField()

    class Meta:
        table = "accounts"