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
DEFAULT_SELL_USER_ID = 2  # or 8

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
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Start migration")
    migration = Migration(cr)

    # General configuration
    migration.setup_configuration()

    # Migration method for each table
    migration.migrate_tbUsers()

    # migration.migrate_tbAnimators()
    # migration.migrate_tbContents()
    # migration.migrate_tbCouponAllowedItems()
    # migration.migrate_tbCoupons()
    # migration.migrate_tbExpenseCategories()
    # migration.migrate_tbGalleryItems()
    # migration.migrate_tbKnowledgeAnswerChoices()
    # migration.migrate_tbKnowledgeAnswerResults()
    # migration.migrate_tbKnowledgeQuestions()
    # migration.migrate_tbKnowledgeTestResults()
    # migration.migrate_tbKnowledgeTests()
    # migration.migrate_tbMailTemplates()
    # migration.migrate_tbStoreCategories()
    # migration.migrate_tbStoreItemAnimators()
    # migration.migrate_tbStoreItemContentPackageMappings()
    # migration.migrate_tbStoreItemContentPackages()
    # migration.migrate_tbStoreItemContents()
    # migration.migrate_tbStoreItemContentTypes()
    # migration.migrate_tbStoreItemPictures()
    # migration.migrate_tbStoreItems()
    # migration.migrate_tbStoreItemTaxes()
    # migration.migrate_tbStoreItemTrainingCourses()
    # migration.migrate_tbStoreItemVariants()
    # migration.migrate_tbStoreShoppingCartItemCoupons()
    # migration.migrate_tbStoreShoppingCartItems()
    # migration.migrate_tbStoreShoppingCartItemTaxes()
    # migration.migrate_tbStoreShoppingCarts()
    # migration.migrate_tbTrainingCourses()

    # Show information about computing migration.
    if migration.lst_generic_email:
        print("Got generic mail :")
        for mail in migration.lst_generic_email:
            print(f"\t{mail}")

    # Print warning
    if migration.lst_warning:
        print("Got warning :")
        for warn in migration.lst_warning:
            print(f"\t{warn}")

    # Print error
    if migration.lst_error:
        print("Got error :")
        for err in migration.lst_error:
            print(f"\t{err}")


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
        self.dct_res_user_id = {}
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
            if table == "tbStoreShoppingCarts":
                str_query = f"""SELECT * FROM {table_name} WHERE IsCompleted = 1 or ProviderStatusText = 'completed';"""
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

    def setup_configuration(self, dry_run=False):
        _logger.info("Setup configuration")

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
        table_name = f"{self.db_name}.dbo.tbAnimators"
        lst_tbl_tbanimators = self.dct_tbl.get(table_name)

        for i, tbanimators in enumerate(lst_tbl_tbanimators):
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

            # TODO Update ID from tbanimators
            dct_tbanimators[tbanimators.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbanimators.ID}"
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
        table_name = f"{self.db_name}.dbo.tbContents"
        lst_tbl_tbcontents = self.dct_tbl.get(table_name)

        for i, tbcontents in enumerate(lst_tbl_tbcontents):
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

            # TODO Update ID from tbcontents
            dct_tbcontents[tbcontents.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbcontents.ID}"
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
        table_name = f"{self.db_name}.dbo.tbCouponAllowedItems"
        lst_tbl_tbcouponalloweditems = self.dct_tbl.get(table_name)

        for i, tbcouponalloweditems in enumerate(lst_tbl_tbcouponalloweditems):
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

            # TODO Update ID from tbcouponalloweditems
            dct_tbcouponalloweditems[
                tbcouponalloweditems.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbcouponalloweditems.ID}"
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
        table_name = f"{self.db_name}.dbo.tbCoupons"
        lst_tbl_tbcoupons = self.dct_tbl.get(table_name)

        for i, tbcoupons in enumerate(lst_tbl_tbcoupons):
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

            # TODO Update ID from tbcoupons
            dct_tbcoupons[tbcoupons.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbcoupons.ID}"
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
        table_name = f"{self.db_name}.dbo.tbExpenseCategories"
        lst_tbl_tbexpensecategories = self.dct_tbl.get(table_name)

        for i, tbexpensecategories in enumerate(lst_tbl_tbexpensecategories):
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

            # TODO Update ID from tbexpensecategories
            dct_tbexpensecategories[
                tbexpensecategories.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbexpensecategories.ID}"
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
        table_name = f"{self.db_name}.dbo.tbGalleryItems"
        lst_tbl_tbgalleryitems = self.dct_tbl.get(table_name)

        for i, tbgalleryitems in enumerate(lst_tbl_tbgalleryitems):
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

            # TODO Update ID from tbgalleryitems
            dct_tbgalleryitems[tbgalleryitems.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbgalleryitems.ID}"
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
        table_name = f"{self.db_name}.dbo.tbKnowledgeAnswerChoices"
        lst_tbl_tbknowledgeanswerchoices = self.dct_tbl.get(table_name)

        for i, tbknowledgeanswerchoices in enumerate(
            lst_tbl_tbknowledgeanswerchoices
        ):
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

            # TODO Update ID from tbknowledgeanswerchoices
            dct_tbknowledgeanswerchoices[
                tbknowledgeanswerchoices.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbknowledgeanswerchoices.ID}"
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
        table_name = f"{self.db_name}.dbo.tbKnowledgeAnswerResults"
        lst_tbl_tbknowledgeanswerresults = self.dct_tbl.get(table_name)

        for i, tbknowledgeanswerresults in enumerate(
            lst_tbl_tbknowledgeanswerresults
        ):
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

            # TODO Update ID from tbknowledgeanswerresults
            dct_tbknowledgeanswerresults[
                tbknowledgeanswerresults.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbknowledgeanswerresults.ID}"
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
        table_name = f"{self.db_name}.dbo.tbKnowledgeQuestions"
        lst_tbl_tbknowledgequestions = self.dct_tbl.get(table_name)

        for i, tbknowledgequestions in enumerate(lst_tbl_tbknowledgequestions):
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

            # TODO Update ID from tbknowledgequestions
            dct_tbknowledgequestions[
                tbknowledgequestions.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbknowledgequestions.ID}"
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
        table_name = f"{self.db_name}.dbo.tbKnowledgeTestResults"
        lst_tbl_tbknowledgetestresults = self.dct_tbl.get(table_name)

        for i, tbknowledgetestresults in enumerate(
            lst_tbl_tbknowledgetestresults
        ):
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

            # TODO Update ID from tbknowledgetestresults
            dct_tbknowledgetestresults[
                tbknowledgetestresults.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbknowledgetestresults.ID}"
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
        table_name = f"{self.db_name}.dbo.tbKnowledgeTests"
        lst_tbl_tbknowledgetests = self.dct_tbl.get(table_name)

        for i, tbknowledgetests in enumerate(lst_tbl_tbknowledgetests):
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

            # TODO Update ID from tbknowledgetests
            dct_tbknowledgetests[tbknowledgetests.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbknowledgetests.ID}"
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
        table_name = f"{self.db_name}.dbo.tbMailTemplates"
        lst_tbl_tbmailtemplates = self.dct_tbl.get(table_name)

        for i, tbmailtemplates in enumerate(lst_tbl_tbmailtemplates):
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

            # TODO Update ID from tbmailtemplates
            dct_tbmailtemplates[tbmailtemplates.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbmailtemplates.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreCategories"
        lst_tbl_tbstorecategories = self.dct_tbl.get(table_name)

        for i, tbstorecategories in enumerate(lst_tbl_tbstorecategories):
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

            # TODO Update ID from tbstorecategories
            dct_tbstorecategories[tbstorecategories.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstorecategories.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemAnimators"
        lst_tbl_tbstoreitemanimators = self.dct_tbl.get(table_name)

        for i, tbstoreitemanimators in enumerate(lst_tbl_tbstoreitemanimators):
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

            # TODO Update ID from tbstoreitemanimators
            dct_tbstoreitemanimators[
                tbstoreitemanimators.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitemanimators.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemContentPackageMappings"
        lst_tbl_tbstoreitemcontentpackagemappings = self.dct_tbl.get(
            table_name
        )

        for i, tbstoreitemcontentpackagemappings in enumerate(
            lst_tbl_tbstoreitemcontentpackagemappings
        ):
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

            # TODO Update ID from tbstoreitemcontentpackagemappings
            dct_tbstoreitemcontentpackagemappings[
                tbstoreitemcontentpackagemappings.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitemcontentpackagemappings.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemContentPackages"
        lst_tbl_tbstoreitemcontentpackages = self.dct_tbl.get(table_name)

        for i, tbstoreitemcontentpackages in enumerate(
            lst_tbl_tbstoreitemcontentpackages
        ):
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

            # TODO Update ID from tbstoreitemcontentpackages
            dct_tbstoreitemcontentpackages[
                tbstoreitemcontentpackages.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitemcontentpackages.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemContents"
        lst_tbl_tbstoreitemcontents = self.dct_tbl.get(table_name)

        for i, tbstoreitemcontents in enumerate(lst_tbl_tbstoreitemcontents):
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

            # TODO Update ID from tbstoreitemcontents
            dct_tbstoreitemcontents[
                tbstoreitemcontents.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitemcontents.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemContentTypes"
        lst_tbl_tbstoreitemcontenttypes = self.dct_tbl.get(table_name)

        for i, tbstoreitemcontenttypes in enumerate(
            lst_tbl_tbstoreitemcontenttypes
        ):
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

            # TODO Update ID from tbstoreitemcontenttypes
            dct_tbstoreitemcontenttypes[
                tbstoreitemcontenttypes.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitemcontenttypes.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemPictures"
        lst_tbl_tbstoreitempictures = self.dct_tbl.get(table_name)

        for i, tbstoreitempictures in enumerate(lst_tbl_tbstoreitempictures):
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

            # TODO Update ID from tbstoreitempictures
            dct_tbstoreitempictures[
                tbstoreitempictures.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitempictures.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItems"
        lst_tbl_tbstoreitems = self.dct_tbl.get(table_name)

        for i, tbstoreitems in enumerate(lst_tbl_tbstoreitems):
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

            # TODO Update ID from tbstoreitems
            dct_tbstoreitems[tbstoreitems.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitems.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemTaxes"
        lst_tbl_tbstoreitemtaxes = self.dct_tbl.get(table_name)

        for i, tbstoreitemtaxes in enumerate(lst_tbl_tbstoreitemtaxes):
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

            # TODO Update ID from tbstoreitemtaxes
            dct_tbstoreitemtaxes[tbstoreitemtaxes.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitemtaxes.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemTrainingCourses"
        lst_tbl_tbstoreitemtrainingcourses = self.dct_tbl.get(table_name)

        for i, tbstoreitemtrainingcourses in enumerate(
            lst_tbl_tbstoreitemtrainingcourses
        ):
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

            # TODO Update ID from tbstoreitemtrainingcourses
            dct_tbstoreitemtrainingcourses[
                tbstoreitemtrainingcourses.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitemtrainingcourses.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreItemVariants"
        lst_tbl_tbstoreitemvariants = self.dct_tbl.get(table_name)

        for i, tbstoreitemvariants in enumerate(lst_tbl_tbstoreitemvariants):
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

            # TODO Update ID from tbstoreitemvariants
            dct_tbstoreitemvariants[
                tbstoreitemvariants.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreitemvariants.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCartItemCoupons"
        lst_tbl_tbstoreshoppingcartitemcoupons = self.dct_tbl.get(table_name)

        for i, tbstoreshoppingcartitemcoupons in enumerate(
            lst_tbl_tbstoreshoppingcartitemcoupons
        ):
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

            # TODO Update ID from tbstoreshoppingcartitemcoupons
            dct_tbstoreshoppingcartitemcoupons[
                tbstoreshoppingcartitemcoupons.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreshoppingcartitemcoupons.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCartItems"
        lst_tbl_tbstoreshoppingcartitems = self.dct_tbl.get(table_name)

        for i, tbstoreshoppingcartitems in enumerate(
            lst_tbl_tbstoreshoppingcartitems
        ):
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

            # TODO Update ID from tbstoreshoppingcartitems
            dct_tbstoreshoppingcartitems[
                tbstoreshoppingcartitems.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreshoppingcartitems.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCartItemTaxes"
        lst_tbl_tbstoreshoppingcartitemtaxes = self.dct_tbl.get(table_name)

        for i, tbstoreshoppingcartitemtaxes in enumerate(
            lst_tbl_tbstoreshoppingcartitemtaxes
        ):
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

            # TODO Update ID from tbstoreshoppingcartitemtaxes
            dct_tbstoreshoppingcartitemtaxes[
                tbstoreshoppingcartitemtaxes.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreshoppingcartitemtaxes.ID}"
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
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCarts"
        lst_tbl_tbstoreshoppingcarts = self.dct_tbl.get(table_name)

        for i, tbstoreshoppingcarts in enumerate(lst_tbl_tbstoreshoppingcarts):
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

            # TODO Update ID from tbstoreshoppingcarts
            dct_tbstoreshoppingcarts[
                tbstoreshoppingcarts.ID
            ] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbstoreshoppingcarts.ID}"
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
        table_name = f"{self.db_name}.dbo.tbTrainingCourses"
        lst_tbl_tbtrainingcourses = self.dct_tbl.get(table_name)

        for i, tbtrainingcourses in enumerate(lst_tbl_tbtrainingcourses):
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

            # TODO Update ID from tbtrainingcourses
            dct_tbtrainingcourses[tbtrainingcourses.ID] = obj_res_partner_id
            # TODO update res.partner to the good model, update
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' id {tbtrainingcourses.ID}"
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
        table_name = f"{self.db_name}.dbo.tbUsers"
        lst_tbl_tbusers = self.dct_tbl.get(table_name)

        for i, tbusers in enumerate(lst_tbl_tbusers):
            pos_id = f"{i}/{len(lst_tbl_tbusers)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            # Ignore user
            if tbusers.UserID == 1231:
                continue

            name = tbusers.FullName
            email = tbusers.Email.lower().strip()
            user_name = tbusers.UserName.lower().strip()

            if email != user_name:
                _logger.warning(
                    f"User name '{user_name}' is different from email"
                    f" '{email}'"
                )
            if not user_name:
                _logger.error(f"Missing user name for membre {tbusers}")

            # Country mapping
            dct_country_mapping = {
                1: 38,
                3: 75,
                11: 7,
                23: 20,
                32: 29,
                45: 43,
                111: 109,
                135: 133,
                179: 177,
                189: 187,
            }
            dct_province_mapping = {
                2: 534,
                5: 536,
                8: 541,
                9: 543,
                12: 538,
                13: 545,
                33: 28,
                35: 42,
                45: 34,
                52: 47,
                58: 53,
                66: -1,  # Martinique is a country
                69: 1675,
                72: -1,  # Haute-Normandie merge to Normandie
                76: 1677,  # Hauts-de-France
                77: 1668,  # Lorraine merge to Grand Est
                78: 1668,  # Alsace merge to Grand Est
                80: 1679,
                81: 1672,
                82: 1019,
                83: 1669,  # Merge to Nouvelle-Aquitaine
                86: 1669,  # Merge to Nouvelle-Aquitaine
                88: 1676,  # Occitanie
                89: 1680,
            }
            # Fix country
            country_id = dct_country_mapping[tbusers.CountryID]
            state_id = dct_province_mapping[tbusers.ProvinceID]
            if state_id == -1:
                if tbusers.ProvinceID == 66:
                    country_id = 149
                    state_id = False
                if tbusers.ProvinceID == 72:
                    state_id = 1668

            # TODO IsAnimator is internal member, else only portal member
            # TODO support DateOfBirth
            # TODO support Gender
            # TODO show lastUpdate migration note field LastUpdatedDate + CreatedDate
            # Info ignore DisplayName, FirstName, Gender, ProperName, LastName, ProviderUserKey, UserId
            # TODO Occupation if exist
            value = {
                "name": name,
                "email": email,
                "state_id": state_id,
                "country_id": country_id,
                "tz": "America/Montreal",
                "create_date": tbusers.CreatedDate,
            }

            if tbusers.AddressLine1 and tbusers.AddressLine1.strip():
                value["street"] = tbusers.AddressLine1.strip()
            if tbusers.AddressLine2 and tbusers.AddressLine2.strip():
                value["street2"] = tbusers.AddressLine2.strip()
            if tbusers.PostalCode and tbusers.PostalCode.strip():
                value["zip"] = tbusers.PostalCode.strip()
            if tbusers.City and tbusers.City.strip():
                value["city"] = tbusers.City.strip()
            if tbusers.WebSite and tbusers.WebSite.strip():
                value["website"] = tbusers.WebSite.strip()
            if tbusers.HomePhone and tbusers.HomePhone.strip():
                value["phone"] = tbusers.HomePhone.strip()
            if tbusers.WorkPhone and tbusers.WorkPhone.strip():
                value["mobile"] = tbusers.WorkPhone.strip()

            obj_partner_id = env["res.partner"].create(value)
            dct_tbusers[tbusers.UserID] = obj_partner_id
            _logger.info(
                f"{pos_id} - res.partner - table {table_name} - ADDED"
                f" '{name}' '{email}' id {tbusers.UserID}"
            )

            # Add to mailing list
            if tbusers.ReceiveNewsletter:
                value_mailing_list_contact = {
                    "name": name,
                    "email": email,
                    "list_ids": [(4, mailing_list_id.id)],
                }
                env["mailing.contact"].create(value_mailing_list_contact)

            # Add message about migration information
            genre = "femme" if tbusers.Gender else "homme"
            comment_message = f"Genre : {genre}<br/>"
            if tbusers.LastUpdatedDate:
                comment_message += (
                    "Dernière modification :"
                    f" {tbusers.LastUpdatedDate.strftime('%Y/%d/%m %H:%M:%S')}<br/>"
                )
            if tbusers.DateOfBirth:
                comment_message += (
                    "Date de naissance :"
                    f" {tbusers.DateOfBirth.strftime('%Y/%d/%m')}<br/>"
                )
            if tbusers.IsAnimator:
                comment_message += f"Est un animateur<br/>"
            if tbusers.Occupation:
                comment_message += f"Occupation : {tbusers.Occupation}<br/>"
            comment_value = {
                "subject": (
                    "Note de migration - Plateforme ASP.net avant migration"
                ),
                "body": f"<p>{comment_message}</p>",
                "parent_id": False,
                "message_type": "comment",
                "author_id": SUPERUSER_ID,
                "model": "res.partner",
                "res_id": obj_partner_id.id,
            }
            env["mail.message"].create(comment_value)

            # Add memo message
            # if membre.Memo:
            #     html_memo = membre.Memo.replace("\n", "<br/>")
            #     comment_message = (
            #         f"<b>Mémo avant migration</b><br/>{html_memo}"
            #     )
            #
            #     comment_value = {
            #         "subject": (
            #             "Mémo avant migration - Plateforme Espace"
            #             " Membre"
            #         ),
            #         "body": f"<p>{comment_message}</p>",
            #         "parent_id": False,
            #         "message_type": "comment",
            #         "author_id": SUPERUSER_ID,
            #         "model": "companie.membre",
            #         "res_id": obj_companie_membre.id,
            #     }
            #     env["mail.message"].create(comment_value)

            if tbusers.UserID == DEFAULT_SELL_USER_ID:
                value = {
                    "name": obj_partner_id.name,
                    "active": True,
                    "login": email,
                    "email": email,
                    # "groups_id": groups_id,
                    # "company_id": company_id.id,
                    # "company_ids": [(4, company_id.id)],
                    "partner_id": obj_partner_id.id,
                }

                obj_user = (
                    env["res.users"]
                    # .with_context(
                    #     {"no_reset_password": no_reset_password}
                    # )
                    .create(value)
                )

                self.dct_res_user_id[tbusers.UserID] = obj_user

        self.dct_tbusers = dct_tbusers
