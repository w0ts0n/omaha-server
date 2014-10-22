# coding: utf8

"""
This software is licensed under the Apache 2 license, quoted below.

Copyright 2014 Crystalnix Limited

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
"""

from django.contrib import admin
from models import Channel, Platform, Application, Version, Action


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'id',)


class ActionInline(admin.StackedInline):
    model = Action
    extra = 0


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    inlines = (ActionInline,)
    list_display = ('app', 'version', 'channel', 'platform',)
    list_filter = ('channel__name', 'platform__name', 'app__name',)
    readonly_fields = ('file_hash',)
