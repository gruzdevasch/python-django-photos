# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-19 06:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_auto_20171119_1331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='postpic',
            field=models.ImageField(blank=True, upload_to=b'static/pic_folder/'),
        ),
    ]
