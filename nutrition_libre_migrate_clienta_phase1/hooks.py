import base64
import datetime
import re
import os

# import locale
import logging
import urllib.parse
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# TODO don't forget to increase memory
# --limit-memory-soft=8589934592 --limit-memory-hard=10737418240

HOST = "localhost"
USER = ""
PORT = "1433"
PASSWD = ""
DB_NAME = ""
PATTERN_FORMATION_NO = r"\b\d+\.\w+\b"
URL_PATTERN_MEDIA = "https://test.ca/media/%s/%s"
URL_PATTERN_FILE = "https://test.ca/file/%s"
PATH_DOWNLOAD = "/tmp/"
DO_DOWNLOAD = True


def post_init_hook(cr, e):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Start migration phase 1")

    migration = Migration(cr)

    migration.migrate(cr)
    migration.download()

    # Print warning
    if migration.lst_warning:
        print("Got warning :")
        lst_warning = list(set(migration.lst_warning))
        lst_warning.sort()
        for warn in lst_warning:
            print(f"\t{warn}")

    # Print error
    if migration.lst_error:
        print("Got error :")
        lst_error = list(set(migration.lst_error))
        lst_error.sort()
        for err in lst_error:
            print(f"\t{err}")


class Struct(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


class Migration:
    def __init__(self, cr):
        # Generic variable
        self.cr = cr
        self.lst_used_email = []
        self.lst_error = []
        self.lst_warning = []

        self.dct_note = {}
        self.dct_url = {}

        # Database information
        import pymssql

        self.host = HOST
        self.user = USER
        self.port = PORT
        self.passwd = PASSWD
        self.db_name = DB_NAME
        self.conn = pymssql.connect(
            server=self.host,
            user=self.user,
            port=self.port,
            password=self.passwd,
            database=self.db_name,
            # charset="utf8",
            # use_unicode=True,
        )
        self.dct_tbl = self._fill_tbl()

    def _fill_tbl(self):
        """
        Fill all database in self.dct_tbl
        :return:
        """
        cur = self.conn.cursor()
        # Get all tables
        str_query = (
            f"""SELECT * FROM {self.db_name}.INFORMATION_SCHEMA.TABLES;"""
        )
        cur.nextset()
        cur.execute(str_query)
        tpl_result = cur.fetchall()

        lst_whitelist_table = [
            "tbAnimators",
            "tbContents",
            "tbCouponAllowedItems",
            "tbCoupons",
            "tbExpenseCategories",
            "tbGalleryItems",
            "tbKnowledgeAnswerChoices",
            "tbKnowledgeAnswerResults",
            "tbKnowledgeQuestions",
            "tbKnowledgeTestResults",
            "tbKnowledgeTests",
            "tbMailTemplates",
            "tbStoreCategories",
            "tbStoreItemAnimators",
            "tbStoreItemContentPackageMappings",
            "tbStoreItemContentPackages",
            "tbStoreItemContents",
            "tbStoreItemContentTypes",
            "tbStoreItemPictures",
            "tbStoreItems",
            "tbStoreItemTaxes",
            "tbStoreItemTrainingCourses",
            "tbStoreItemVariants",
            "tbStoreShoppingCartItemCoupons",
            "tbStoreShoppingCartItems",
            "tbStoreShoppingCartItemTaxes",
            "tbStoreShoppingCarts",
            "tbTrainingCourses",
            "tbUsers",
        ]

        dct_tbl = {f"{a[0]}.{a[1]}.{a[2]}": [] for a in tpl_result}
        dct_short_tbl = {f"{a[0]}.{a[1]}.{a[2]}": a[2] for a in tpl_result}

        for table_name, lst_column in dct_tbl.items():
            table = dct_short_tbl[table_name]
            if table not in lst_whitelist_table:
                # msg = f"Skip table '{table}'"
                # _logger.warning(msg)
                # self.lst_warning.append(msg)
                continue

            _logger.info(f"Import in cache table '{table}'")
            str_query = f"""SELECT COLUMN_NAME FROM {self.db_name}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'{table}';"""
            cur.nextset()
            cur.execute(str_query)
            tpl_result = cur.fetchall()
            lst_column_name = [a[0] for a in tpl_result]
            if table == "tbStoreShoppingCarts":
                # str_query = f"""SELECT * FROM {table_name} WHERE IsCompleted = 1 or ProviderStatusText = 'completed';"""
                str_query = f"""SELECT * FROM {table_name} WHERE ProviderStatusText = 'completed' ORDER BY CartID;"""
            else:
                str_query = f"""SELECT * FROM {table_name};"""
            cur.nextset()
            cur.execute(str_query)
            tpl_result = cur.fetchall()

            for lst_result in tpl_result:
                i = -1
                dct_value = {}
                for result in lst_result:
                    i += 1
                    dct_value[lst_column_name[i]] = result
                lst_column.append(Struct(**dct_value))

        return dct_tbl

    def migrate(self, cr):
        env = api.Environment(cr, SUPERUSER_ID, {})
        slide_channel_ids = env["slide.channel"].search([])
        lst_course = []
        for slide_channel_id in slide_channel_ids:
            match = re.search(PATTERN_FORMATION_NO, slide_channel_id.name)
            if match:
                course_no = match.group()
                lst_course.append(course_no)

        tbl_store_item = self.dct_tbl[f"{self.db_name}.dbo.tbStoreItems"]
        dct_store_item = {a.ItemID: a for a in tbl_store_item}
        tbl_store_item_contents = self.dct_tbl[
            f"{self.db_name}.dbo.tbStoreItemContents"
        ]
        tbl_store_item_content_package_mapping = self.dct_tbl[
            f"{self.db_name}.dbo.tbStoreItemContentPackageMappings"
        ]
        tbl_store_item_content_packages = self.dct_tbl[
            f"{self.db_name}.dbo.tbStoreItemContentPackages"
        ]
        dct_content_packages = {
            a.PackageID: a for a in tbl_store_item_content_packages
        }
        # for package in tbl_store_item_content_packages:
        #     dct_content_packages[package.PackageID] = package

        dct_mapping_content_package = {}
        dct_mapping_package_item = {}
        mega_list_store_item_id = []
        for store_item_content_package in tbl_store_item_content_packages:
            lst_store_item_id = [
                a.ItemID
                for a in tbl_store_item_content_package_mapping
                if a.PackageID == store_item_content_package.PackageID
            ]
            mega_list_store_item_id.extend(lst_store_item_id)
            dct_mapping_package_item[store_item_content_package.PackageID] = (
                lst_store_item_id
            )
            for item_id in lst_store_item_id:
                dct_mapping_content_package[item_id] = (
                    store_item_content_package
                )

        mega_list_store_item_id.sort()

        for store_item_content in tbl_store_item_contents:
            match = None
            key = None
            url = None
            note = None

            # Detect if course or general item, by item name or package name
            store_item_ids = dct_mapping_package_item[
                store_item_content.PackageID
            ]
            package = dct_content_packages.get(store_item_content.PackageID)
            if store_item_ids:
                first_item_name = dct_store_item[store_item_ids[0]].ItemNameFR
                match = re.search(PATTERN_FORMATION_NO, first_item_name)
            else:
                if store_item_content.ContentBodyFR:
                    match = re.search(
                        PATTERN_FORMATION_NO, store_item_content.ContentBodyFR
                    )
                if not match:
                    match = re.search(
                        PATTERN_FORMATION_NO, store_item_content.ContentTitleFR
                    )
                if not match:
                    match = re.search(
                        PATTERN_FORMATION_NO, package.PackageName
                    )
            is_general = False
            if match:
                no_formation = match.group()
            else:
                is_general = True
                no_formation = "Général"

            sub_key = f"{no_formation}#" if not is_general else f"general#"
            if store_item_content.ContentTypeID in (3,):
                # Video, file
                url = URL_PATTERN_MEDIA % (
                    package.PackageKey,
                    urllib.parse.quote(store_item_content.ContentFileName),
                )
                key = f"{sub_key}{package.PackageKey}#{store_item_content.ContentFileName}"
            elif store_item_content.ContentTypeID in (1,):
                note = store_item_content.ContentBodyFR
                key = f"{sub_key}{package.PackageKey}#{store_item_content.ContentTitleFR}"
            elif store_item_content.ContentTypeID in (2,):
                url = URL_PATTERN_FILE % urllib.parse.quote(
                    store_item_content.ContentFileName
                )
                key = f"{sub_key}{package.PackageKey}#{store_item_content.ContentTitleFR}"
            elif store_item_content.ContentTypeID not in (1, 2, 3):
                print("ok")
            else:
                raise Exception("fd")
                print("not supported")
            if store_item_content.ContentTypeID in (
                2,
                3,
            ):
                if key and url and key in self.dct_url.keys():
                    msg = f"Key dupliqué pour les URL, key {key}, old value '{self.dct_url[key]}', new value '{url}'"
                    _logger.warning(msg)
                    self.lst_warning.append(msg)
                self.dct_url[key] = url
            else:
                if key and key in self.dct_url.keys():
                    msg = f"Key dupliqué, key {key}, old value '{self.dct_note[key]}', new value '{note}'"
                    _logger.warning(msg)
                    self.lst_warning.append(msg)
                self.dct_note[key] = note
        return self.dct_url, self.dct_note

    def download(self):
        lst_dir = set()
        lst_cmd_download = []
        lst_cmd_note = []
        cmd_cd = "cd '%s'"
        # cmd_download = "axel -n10 -o %s %s"
        cmd_download = "axel -n10 '%s'"
        for key, value in self.dct_url.items():
            # match = re.search(PATTERN_FORMATION_NO, key)
            # if match:
            #     course_no = match.group()
            # else:
            #     dir_name, title, url = key.split("#", 3)
            dir_name, title, name = key.split("#", 3)
            new_title = title.replace(" ", "_")
            if dir_name == "general":
                dir_path = os.path.join(PATH_DOWNLOAD, dir_name)
            else:
                dir_path = os.path.join(
                    PATH_DOWNLOAD, f"{dir_name}_{new_title}"
                )
            lst_dir.add(dir_path)
            # lst_cmd.append(cmd_cd % name)
            # cmd_download_fill = cmd_download % (name, value)
            cmd_download_fill = cmd_download % value
            cmd = f"{cmd_cd % dir_path};{cmd_download_fill}"
            file_name = os.path.join(
                dir_path, urllib.parse.unquote(value.rsplit("/", 1)[1])
            )
            lst_cmd_download.append((cmd, file_name))

        for key, value in self.dct_note.items():
            dir_name, title, name = key.split("#", 3)
            new_title = title.replace(" ", "_")
            if dir_name == "general":
                dir_path = os.path.join(PATH_DOWNLOAD, dir_name)
            else:
                dir_path = os.path.join(
                    PATH_DOWNLOAD, f"{dir_name}_{new_title}"
                )
            lst_dir.add(dir_path)
            lst_cmd_note.append((dir_path, value))

        # Create directory
        for dir_name in lst_dir:
            cmd = f"mkdir -p '{dir_name}'"
            os.system(cmd)

        # Create associate notes
        for dir_path, value in lst_cmd_note:
            file_path = os.path.join(dir_path, "note.txt")
            if os.path.isfile(file_path):
                continue
            with open(file_path, "w") as file:
                file.write(value)

        # Create associate download file
        if DO_DOWNLOAD:
            for cmd, file_path in lst_cmd_download:
                if os.path.isfile(file_path):
                    continue
                print(f"Download {file_path} with cmd {cmd}")
                os.system(cmd)
                print(f"End of download {file_path} with cmd {cmd}")
        print("End of download")
