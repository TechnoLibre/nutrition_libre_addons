import logging
import os

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
BACKUP_PATH = "/tmp/"
FILE_PATH = f"{BACKUP_PATH}/document/doc"
DEBUG_LIMIT = False
LIMIT = 20
GENERIC_EMAIL = f"%s_membre@exemple.ca"

try:
    import pymssql

    assert pymssql
except ImportError:
    raise ValidationError(
        'pymssql is not available. Please install "pymssql" python package.'
    )
if not HOST or not USER or not PASSWD or not DB_NAME:
    raise ValidationError(
        f"Please, fill constant HOST/USER/PASSWD/DB_NAME into files {__file__}"
    )


def post_init_hook(cr, e):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        _logger.info("Start migration")


class Struct(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


class Migration:
    def __init__(self, cr):
        # Generic variable
        self.cr = cr
        self.lst_generic_email = []
        self.lst_used_email = []
        self.lst_error = []
        self.lst_warning = []

        # Path of the backup
        self.source_code_path = BACKUP_PATH
        self.logo_path = f"{self.source_code_path}/images/logo"
        # Table into cache
        self.dct_tbanimators = {}
        self.dct_tbcontents = {}
        self.dct_tbcouponalloweditems = {}
        self.dct_tbcoupons = {}
        self.dct_tbexpensecategories = {}
        self.dct_tbgalleryitems = {}
        self.dct_tbknowledgeanswerchoices = {}
        self.dct_tbknowledgeanswerresults = {}
        self.dct_tbknowledgequestions = {}
        self.dct_tbknowledgetestresults = {}
        self.dct_tbknowledgetests = {}
        self.dct_tbmailtemplates = {}
        self.dct_tbstorecategories = {}
        self.dct_tbstoreitemanimators = {}
        self.dct_tbstoreitemcontentpackagemappings = {}
        self.dct_tbstoreitemcontentpackages = {}
        self.dct_tbstoreitemcontents = {}
        self.dct_tbstoreitemcontenttypes = {}
        self.dct_tbstoreitempictures = {}
        self.dct_tbstoreitems = {}
        self.dct_tbstoreitemtaxes = {}
        self.dct_tbstoreitemtrainingcourses = {}
        self.dct_tbstoreitemvariants = {}
        self.dct_tbstoreshoppingcartitemcoupons = {}
        self.dct_tbstoreshoppingcartitems = {}
        self.dct_tbstoreshoppingcartitemtaxes = {}
        self.dct_tbstoreshoppingcarts = {}
        self.dct_tbtrainingcourses = {}
        self.dct_tbusers = {}
        # Model into cache
        self.dct_partner_id = {}
        # Database information
        assert pymssql
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
                msg = f"Skip table '{table}'"
                _logger.warning(msg)
                self.lst_warning.append(msg)
                continue

            _logger.info(f"Import in cache table '{table}'")
            str_query = f"""SELECT COLUMN_NAME FROM {self.db_name}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'{table}';"""
            cur.nextset()
            cur.execute(str_query)
            tpl_result = cur.fetchall()
            lst_column_name = [a[0] for a in tpl_result]
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

    def setup_configuration(self, dry_run=False):
        _logger.info("Setup configuration")

        with api.Environment.manage():

            env = api.Environment(self.cr, SUPERUSER_ID, {})
            # General configuration
            values = {
                # 'use_quotation_validity_days': True,
                # 'quotation_validity_days': 30,
                # 'portal_confirmation_sign': True,
                # 'portal_invoice_confirmation_sign': True,
                # 'group_sale_delivery_address': True,
                # 'group_sale_order_template': True,
                # 'default_sale_order_template_id': True,
            }
            if not dry_run:
                event_config = env["res.config.settings"].sudo().create(values)
                event_config.execute()

    def migrate_tbAnimators(self):
        """
        :return:
        """
        _logger.info("Migrate tbAnimators")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbanimators:
            return
        dct_tbanimators = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbAnimators"
        lst_tbl_tbanimators = self.dct_tbl.get(table_name)

        for tbanimators in lst_tbl_tbanimators:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbanimators)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbanimators.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbanimators
            dct_tbanimators[lst_tbl_tbanimators.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbanimators.ID}"
            )

        self.dct_tbanimators = dct_tbanimators

    def migrate_tbContents(self):
        """
        :return:
        """
        _logger.info("Migrate tbContents")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbcontents:
            return
        dct_tbcontents = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbContents"
        lst_tbl_tbcontents = self.dct_tbl.get(table_name)

        for tbcontents in lst_tbl_tbcontents:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbcontents)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbcontents.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbcontents
            dct_tbcontents[lst_tbl_tbcontents.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbcontents.ID}"
            )

        self.dct_tbcontents = dct_tbcontents

    def migrate_tbCouponAllowedItems(self):
        """
        :return:
        """
        _logger.info("Migrate tbCouponAllowedItems")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbcouponalloweditems:
            return
        dct_tbcouponalloweditems = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbCouponAllowedItems"
        lst_tbl_tbcouponalloweditems = self.dct_tbl.get(table_name)

        for tbcouponalloweditems in lst_tbl_tbcouponalloweditems:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbcouponalloweditems)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbcouponalloweditems.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbcouponalloweditems
            dct_tbcouponalloweditems[
                lst_tbl_tbcouponalloweditems.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbcouponalloweditems.ID}"
            )

        self.dct_tbcouponalloweditems = dct_tbcouponalloweditems

    def migrate_tbCoupons(self):
        """
        :return:
        """
        _logger.info("Migrate tbCoupons")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbcoupons:
            return
        dct_tbcoupons = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbCoupons"
        lst_tbl_tbcoupons = self.dct_tbl.get(table_name)

        for tbcoupons in lst_tbl_tbcoupons:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbcoupons)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbcoupons.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbcoupons
            dct_tbcoupons[lst_tbl_tbcoupons.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbcoupons.ID}"
            )

        self.dct_tbcoupons = dct_tbcoupons

    def migrate_tbExpenseCategories(self):
        """
        :return:
        """
        _logger.info("Migrate tbExpenseCategories")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbexpensecategories:
            return
        dct_tbexpensecategories = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbExpenseCategories"
        lst_tbl_tbexpensecategories = self.dct_tbl.get(table_name)

        for tbexpensecategories in lst_tbl_tbexpensecategories:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbexpensecategories)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbexpensecategories.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbexpensecategories
            dct_tbexpensecategories[
                lst_tbl_tbexpensecategories.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbexpensecategories.ID}"
            )

        self.dct_tbexpensecategories = dct_tbexpensecategories

    def migrate_tbGalleryItems(self):
        """
        :return:
        """
        _logger.info("Migrate tbGalleryItems")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbgalleryitems:
            return
        dct_tbgalleryitems = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbGalleryItems"
        lst_tbl_tbgalleryitems = self.dct_tbl.get(table_name)

        for tbgalleryitems in lst_tbl_tbgalleryitems:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbgalleryitems)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbgalleryitems.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbgalleryitems
            dct_tbgalleryitems[lst_tbl_tbgalleryitems.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbgalleryitems.ID}"
            )

        self.dct_tbgalleryitems = dct_tbgalleryitems

    def migrate_tbKnowledgeAnswerChoices(self):
        """
        :return:
        """
        _logger.info("Migrate tbKnowledgeAnswerChoices")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbknowledgeanswerchoices:
            return
        dct_tbknowledgeanswerchoices = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbKnowledgeAnswerChoices"
        lst_tbl_tbknowledgeanswerchoices = self.dct_tbl.get(table_name)

        for tbknowledgeanswerchoices in lst_tbl_tbknowledgeanswerchoices:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbknowledgeanswerchoices)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbknowledgeanswerchoices.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbknowledgeanswerchoices
            dct_tbknowledgeanswerchoices[
                lst_tbl_tbknowledgeanswerchoices.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbknowledgeanswerchoices.ID}"
            )

        self.dct_tbknowledgeanswerchoices = dct_tbknowledgeanswerchoices

    def migrate_tbKnowledgeAnswerResults(self):
        """
        :return:
        """
        _logger.info("Migrate tbKnowledgeAnswerResults")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbknowledgeanswerresults:
            return
        dct_tbknowledgeanswerresults = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbKnowledgeAnswerResults"
        lst_tbl_tbknowledgeanswerresults = self.dct_tbl.get(table_name)

        for tbknowledgeanswerresults in lst_tbl_tbknowledgeanswerresults:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbknowledgeanswerresults)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbknowledgeanswerresults.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbknowledgeanswerresults
            dct_tbknowledgeanswerresults[
                lst_tbl_tbknowledgeanswerresults.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbknowledgeanswerresults.ID}"
            )

        self.dct_tbknowledgeanswerresults = dct_tbknowledgeanswerresults

    def migrate_tbKnowledgeQuestions(self):
        """
        :return:
        """
        _logger.info("Migrate tbKnowledgeQuestions")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbknowledgequestions:
            return
        dct_tbknowledgequestions = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbKnowledgeQuestions"
        lst_tbl_tbknowledgequestions = self.dct_tbl.get(table_name)

        for tbknowledgequestions in lst_tbl_tbknowledgequestions:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbknowledgequestions)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbknowledgequestions.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbknowledgequestions
            dct_tbknowledgequestions[
                lst_tbl_tbknowledgequestions.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbknowledgequestions.ID}"
            )

        self.dct_tbknowledgequestions = dct_tbknowledgequestions

    def migrate_tbKnowledgeTestResults(self):
        """
        :return:
        """
        _logger.info("Migrate tbKnowledgeTestResults")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbknowledgetestresults:
            return
        dct_tbknowledgetestresults = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbKnowledgeTestResults"
        lst_tbl_tbknowledgetestresults = self.dct_tbl.get(table_name)

        for tbknowledgetestresults in lst_tbl_tbknowledgetestresults:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbknowledgetestresults)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbknowledgetestresults.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbknowledgetestresults
            dct_tbknowledgetestresults[
                lst_tbl_tbknowledgetestresults.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbknowledgetestresults.ID}"
            )

        self.dct_tbknowledgetestresults = dct_tbknowledgetestresults

    def migrate_tbKnowledgeTests(self):
        """
        :return:
        """
        _logger.info("Migrate tbKnowledgeTests")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbknowledgetests:
            return
        dct_tbknowledgetests = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbKnowledgeTests"
        lst_tbl_tbknowledgetests = self.dct_tbl.get(table_name)

        for tbknowledgetests in lst_tbl_tbknowledgetests:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbknowledgetests)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbknowledgetests.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbknowledgetests
            dct_tbknowledgetests[
                lst_tbl_tbknowledgetests.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbknowledgetests.ID}"
            )

        self.dct_tbknowledgetests = dct_tbknowledgetests

    def migrate_tbMailTemplates(self):
        """
        :return:
        """
        _logger.info("Migrate tbMailTemplates")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbmailtemplates:
            return
        dct_tbmailtemplates = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbMailTemplates"
        lst_tbl_tbmailtemplates = self.dct_tbl.get(table_name)

        for tbmailtemplates in lst_tbl_tbmailtemplates:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbmailtemplates)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbmailtemplates.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbmailtemplates
            dct_tbmailtemplates[
                lst_tbl_tbmailtemplates.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbmailtemplates.ID}"
            )

        self.dct_tbmailtemplates = dct_tbmailtemplates

    def migrate_tbStoreCategories(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreCategories")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstorecategories:
            return
        dct_tbstorecategories = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreCategories"
        lst_tbl_tbstorecategories = self.dct_tbl.get(table_name)

        for tbstorecategories in lst_tbl_tbstorecategories:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstorecategories)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstorecategories.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstorecategories
            dct_tbstorecategories[
                lst_tbl_tbstorecategories.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstorecategories.ID}"
            )

        self.dct_tbstorecategories = dct_tbstorecategories

    def migrate_tbStoreItemAnimators(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemAnimators")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitemanimators:
            return
        dct_tbstoreitemanimators = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemAnimators"
        lst_tbl_tbstoreitemanimators = self.dct_tbl.get(table_name)

        for tbstoreitemanimators in lst_tbl_tbstoreitemanimators:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitemanimators)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitemanimators.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitemanimators
            dct_tbstoreitemanimators[
                lst_tbl_tbstoreitemanimators.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitemanimators.ID}"
            )

        self.dct_tbstoreitemanimators = dct_tbstoreitemanimators

    def migrate_tbStoreItemContentPackageMappings(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemContentPackageMappings")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitemcontentpackagemappings:
            return
        dct_tbstoreitemcontentpackagemappings = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemContentPackageMappings"
        lst_tbl_tbstoreitemcontentpackagemappings = self.dct_tbl.get(
            table_name
        )

        for (
            tbstoreitemcontentpackagemappings
        ) in lst_tbl_tbstoreitemcontentpackagemappings:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitemcontentpackagemappings)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitemcontentpackagemappings.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitemcontentpackagemappings
            dct_tbstoreitemcontentpackagemappings[
                lst_tbl_tbstoreitemcontentpackagemappings.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitemcontentpackagemappings.ID}"
            )

        self.dct_tbstoreitemcontentpackagemappings = (
            dct_tbstoreitemcontentpackagemappings
        )

    def migrate_tbStoreItemContentPackages(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemContentPackages")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitemcontentpackages:
            return
        dct_tbstoreitemcontentpackages = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemContentPackages"
        lst_tbl_tbstoreitemcontentpackages = self.dct_tbl.get(table_name)

        for tbstoreitemcontentpackages in lst_tbl_tbstoreitemcontentpackages:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitemcontentpackages)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitemcontentpackages.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitemcontentpackages
            dct_tbstoreitemcontentpackages[
                lst_tbl_tbstoreitemcontentpackages.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitemcontentpackages.ID}"
            )

        self.dct_tbstoreitemcontentpackages = dct_tbstoreitemcontentpackages

    def migrate_tbStoreItemContents(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemContents")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitemcontents:
            return
        dct_tbstoreitemcontents = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemContents"
        lst_tbl_tbstoreitemcontents = self.dct_tbl.get(table_name)

        for tbstoreitemcontents in lst_tbl_tbstoreitemcontents:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitemcontents)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitemcontents.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitemcontents
            dct_tbstoreitemcontents[
                lst_tbl_tbstoreitemcontents.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitemcontents.ID}"
            )

        self.dct_tbstoreitemcontents = dct_tbstoreitemcontents

    def migrate_tbStoreItemContentTypes(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemContentTypes")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitemcontenttypes:
            return
        dct_tbstoreitemcontenttypes = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemContentTypes"
        lst_tbl_tbstoreitemcontenttypes = self.dct_tbl.get(table_name)

        for tbstoreitemcontenttypes in lst_tbl_tbstoreitemcontenttypes:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitemcontenttypes)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitemcontenttypes.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitemcontenttypes
            dct_tbstoreitemcontenttypes[
                lst_tbl_tbstoreitemcontenttypes.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitemcontenttypes.ID}"
            )

        self.dct_tbstoreitemcontenttypes = dct_tbstoreitemcontenttypes

    def migrate_tbStoreItemPictures(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemPictures")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitempictures:
            return
        dct_tbstoreitempictures = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemPictures"
        lst_tbl_tbstoreitempictures = self.dct_tbl.get(table_name)

        for tbstoreitempictures in lst_tbl_tbstoreitempictures:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitempictures)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitempictures.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitempictures
            dct_tbstoreitempictures[
                lst_tbl_tbstoreitempictures.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitempictures.ID}"
            )

        self.dct_tbstoreitempictures = dct_tbstoreitempictures

    def migrate_tbStoreItems(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItems")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitems:
            return
        dct_tbstoreitems = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItems"
        lst_tbl_tbstoreitems = self.dct_tbl.get(table_name)

        for tbstoreitems in lst_tbl_tbstoreitems:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitems)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitems.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitems
            dct_tbstoreitems[lst_tbl_tbstoreitems.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitems.ID}"
            )

        self.dct_tbstoreitems = dct_tbstoreitems

    def migrate_tbStoreItemTaxes(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemTaxes")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitemtaxes:
            return
        dct_tbstoreitemtaxes = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemTaxes"
        lst_tbl_tbstoreitemtaxes = self.dct_tbl.get(table_name)

        for tbstoreitemtaxes in lst_tbl_tbstoreitemtaxes:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitemtaxes)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitemtaxes.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitemtaxes
            dct_tbstoreitemtaxes[
                lst_tbl_tbstoreitemtaxes.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitemtaxes.ID}"
            )

        self.dct_tbstoreitemtaxes = dct_tbstoreitemtaxes

    def migrate_tbStoreItemTrainingCourses(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemTrainingCourses")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitemtrainingcourses:
            return
        dct_tbstoreitemtrainingcourses = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemTrainingCourses"
        lst_tbl_tbstoreitemtrainingcourses = self.dct_tbl.get(table_name)

        for tbstoreitemtrainingcourses in lst_tbl_tbstoreitemtrainingcourses:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitemtrainingcourses)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitemtrainingcourses.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitemtrainingcourses
            dct_tbstoreitemtrainingcourses[
                lst_tbl_tbstoreitemtrainingcourses.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitemtrainingcourses.ID}"
            )

        self.dct_tbstoreitemtrainingcourses = dct_tbstoreitemtrainingcourses

    def migrate_tbStoreItemVariants(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItemVariants")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreitemvariants:
            return
        dct_tbstoreitemvariants = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreItemVariants"
        lst_tbl_tbstoreitemvariants = self.dct_tbl.get(table_name)

        for tbstoreitemvariants in lst_tbl_tbstoreitemvariants:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreitemvariants)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreitemvariants.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreitemvariants
            dct_tbstoreitemvariants[
                lst_tbl_tbstoreitemvariants.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreitemvariants.ID}"
            )

        self.dct_tbstoreitemvariants = dct_tbstoreitemvariants

    def migrate_tbStoreShoppingCartItemCoupons(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreShoppingCartItemCoupons")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreshoppingcartitemcoupons:
            return
        dct_tbstoreshoppingcartitemcoupons = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCartItemCoupons"
        lst_tbl_tbstoreshoppingcartitemcoupons = self.dct_tbl.get(table_name)

        for (
            tbstoreshoppingcartitemcoupons
        ) in lst_tbl_tbstoreshoppingcartitemcoupons:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreshoppingcartitemcoupons)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreshoppingcartitemcoupons.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreshoppingcartitemcoupons
            dct_tbstoreshoppingcartitemcoupons[
                lst_tbl_tbstoreshoppingcartitemcoupons.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreshoppingcartitemcoupons.ID}"
            )

        self.dct_tbstoreshoppingcartitemcoupons = (
            dct_tbstoreshoppingcartitemcoupons
        )

    def migrate_tbStoreShoppingCartItems(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreShoppingCartItems")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreshoppingcartitems:
            return
        dct_tbstoreshoppingcartitems = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCartItems"
        lst_tbl_tbstoreshoppingcartitems = self.dct_tbl.get(table_name)

        for tbstoreshoppingcartitems in lst_tbl_tbstoreshoppingcartitems:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreshoppingcartitems)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreshoppingcartitems.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreshoppingcartitems
            dct_tbstoreshoppingcartitems[
                lst_tbl_tbstoreshoppingcartitems.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreshoppingcartitems.ID}"
            )

        self.dct_tbstoreshoppingcartitems = dct_tbstoreshoppingcartitems

    def migrate_tbStoreShoppingCartItemTaxes(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreShoppingCartItemTaxes")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreshoppingcartitemtaxes:
            return
        dct_tbstoreshoppingcartitemtaxes = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCartItemTaxes"
        lst_tbl_tbstoreshoppingcartitemtaxes = self.dct_tbl.get(table_name)

        for (
            tbstoreshoppingcartitemtaxes
        ) in lst_tbl_tbstoreshoppingcartitemtaxes:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreshoppingcartitemtaxes)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreshoppingcartitemtaxes.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreshoppingcartitemtaxes
            dct_tbstoreshoppingcartitemtaxes[
                lst_tbl_tbstoreshoppingcartitemtaxes.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreshoppingcartitemtaxes.ID}"
            )

        self.dct_tbstoreshoppingcartitemtaxes = (
            dct_tbstoreshoppingcartitemtaxes
        )

    def migrate_tbStoreShoppingCarts(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreShoppingCarts")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbstoreshoppingcarts:
            return
        dct_tbstoreshoppingcarts = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCarts"
        lst_tbl_tbstoreshoppingcarts = self.dct_tbl.get(table_name)

        for tbstoreshoppingcarts in lst_tbl_tbstoreshoppingcarts:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbstoreshoppingcarts)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbstoreshoppingcarts.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbstoreshoppingcarts
            dct_tbstoreshoppingcarts[
                lst_tbl_tbstoreshoppingcarts.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbstoreshoppingcarts.ID}"
            )

        self.dct_tbstoreshoppingcarts = dct_tbstoreshoppingcarts

    def migrate_tbTrainingCourses(self):
        """
        :return:
        """
        _logger.info("Migrate tbTrainingCourses")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbtrainingcourses:
            return
        dct_tbtrainingcourses = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbTrainingCourses"
        lst_tbl_tbtrainingcourses = self.dct_tbl.get(table_name)

        for tbtrainingcourses in lst_tbl_tbtrainingcourses:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbtrainingcourses)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbtrainingcourses.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbtrainingcourses
            dct_tbtrainingcourses[
                lst_tbl_tbtrainingcourses.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbtrainingcourses.ID}"
            )

        self.dct_tbtrainingcourses = dct_tbtrainingcourses

    def migrate_tbUsers(self):
        """
        :return:
        """
        _logger.info("Migrate tbUsers")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_tbusers:
            return
        dct_tbusers = {}
        i = 0
        table_name = f"{self.db_name}.dbo.tbUsers"
        lst_tbl_tbusers = self.dct_tbl.get(table_name)

        for tbusers in lst_tbl_tbusers:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_tbusers)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # TODO update variable name from database table
            # name = tbusers.Name
            name = ""

            value = {
                "name": name,
            }

            # TODO update model name
            obj_res_partner_id = env["res.partner"].create(value)

            # TODO Update ID from lst_tbl_tbusers
            dct_tbusers[lst_tbl_tbusers.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {lst_tbl_tbusers.ID}"
            )

        self.dct_tbusers = dct_tbusers
