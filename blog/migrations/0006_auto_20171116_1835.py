# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-16 11:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_auto_20171116_1748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='postpic',
            field=models.ImageField(default=b'pic_folder/None/default_profile_picture.png', upload_to=b'pic_folder/'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='profpic',
            field=models.ImageField(default=b'pic_folder/None/default_profile_picture.png', upload_to=b'pic_folder/'),
        ),
    ]
