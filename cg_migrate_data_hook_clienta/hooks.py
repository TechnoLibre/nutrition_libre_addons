import datetime
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
DEBUG_OUTPUT = True
DEBUG_LIMIT = False
LIMIT = 20
DEFAULT_SELL_USER_ID = 2  # or 8
MIGRATE_INVOICE = False

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
    # migration.migrate_tbExpenseCategories()
    # migration.migrate_tbGalleryItems()
    # migration.migrate_tbKnowledgeAnswerChoices()
    # migration.migrate_tbKnowledgeAnswerResults()
    # migration.migrate_tbKnowledgeQuestions()
    # migration.migrate_tbKnowledgeTestResults()
    # migration.migrate_tbKnowledgeTests()
    # migration.migrate_tbMailTemplates()
    migration.migrate_tbStoreCategories()
    migration.migrate_tbTrainingCourses()
    for (
        obj_id_i,
        obj_slide_channel_id,
    ) in migration.dct_k_tbtrainingcourses_v_slide_channel.items():
        (
            obj_survey_id,
            first_knowledge_test_id,
        ) = migration.continue_migrate_tbTrainingCourses_knowledge_question(
            obj_slide_channel_id,
            obj_id_i,
        )
        if obj_survey_id is False or first_knowledge_test_id is False:
            continue
        migration.continue_migrate_tbTrainingCourses_slide_slide(
            first_knowledge_test_id,
            obj_slide_channel_id,
            obj_survey_id,
        )

    migration.continue_migrate_tbTrainingCourses_knownledge_answer()
    # migration.migrate_tbStoreItemAnimators()
    # migration.migrate_tbStoreItemContentPackageMappings()
    # migration.migrate_tbStoreItemContentPackages()
    # migration.migrate_tbStoreItemContents()
    # migration.migrate_tbStoreItemContentTypes()
    # migration.migrate_tbStoreItemPictures()
    migration.migrate_tbStoreItems()
    # migration.migrate_tbStoreItemTaxes()
    # migration.migrate_tbStoreItemTrainingCourses()
    # migration.migrate_tbStoreItemVariants()
    # migration.migrate_tbStoreShoppingCartItemCoupons()
    # migration.migrate_tbStoreShoppingCartItems()
    # migration.migrate_tbStoreShoppingCartItemTaxes()
    migration.migrate_tbStoreShoppingCarts()
    migration.migrate_tbCoupons()

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

    # Print summary
    lst_model = [
        "res.partner",
        "res.users",
        "product.category",
        "slide.channel",
        "survey.survey",
        "survey.question",
        "survey.question.answer",
        "slide.slide",
        "survey.user_input",
        "survey.user_input.line",
        "slide.channel.partner",
        "slide.slide.partner",
        "event.event",
        "event.event.ticket",
        "product.template",
        "sale.order",
        "sale.order.line",
        "event.registration",
        "account.move",
        "account.payment",
        "loyalty.program",
        "loyalty.reward",
    ]
    print(f"Migrate into {len(lst_model)} models.")
    for model in lst_model:
        print(f"{len(env[model].search([]))} {model}")


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

        # Path of the backup
        self.source_code_path = BACKUP_PATH
        self.logo_path = f"{self.source_code_path}/images/logo"
        # Table into cache
        self.dct_tbanimators = {}
        self.dct_tbcontents = {}
        self.dct_tbcouponalloweditems = {}
        self.dct_k_tbcoupons_v_loyalty_program = {}
        self.dct_tbexpensecategories = {}
        self.dct_tbgalleryitems = {}
        self.dct_k_tbknowledgeanswerresults_v_survey_question_answer = {}
        self.dct_k_tbknowledgequestions_v_survey_question = {}
        self.dct_tbknowledgetestresults = {}
        self.dct_tbknowledgetests = {}
        self.dct_tbmailtemplates = {}
        self.dct_k_tbstorecategories_v_product_category = {}
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
        self.dct_k_tbstoreshoppingcarts_v_sale_order = {}
        self.dct_k_tbtrainingcourses_v_slide_channel = {}
        self.dct_tbusers = {}
        # Model into cache
        self.dct_res_user_id = {}
        self.dct_partner_id = {}
        self.dct_k_knowledgetest_v_survey_id = {}
        self.dct_k_survey_v_slide_survey_id = {}
        self.dct_event = {}
        self.dct_event_ticket = {}
        self.dct_k_tbstoreitems_v_product_template = {}
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
        model_name = "res.partner"

        for i, tbanimators in enumerate(lst_tbl_tbanimators):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbanimators)}"
            # TODO update variable name from database table
            obj_id_i = tbanimators.ID
            # name = tbanimators.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbanimators[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbcontents in enumerate(lst_tbl_tbcontents):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbcontents)}"
            # TODO update variable name from database table
            obj_id_i = tbcontents.ID
            # name = tbcontents.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbcontents[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbcouponalloweditems in enumerate(lst_tbl_tbcouponalloweditems):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbcouponalloweditems)}"
            # TODO update variable name from database table
            obj_id_i = tbcouponalloweditems.ID
            # name = tbcouponalloweditems.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbcouponalloweditems[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

        self.dct_tbcouponalloweditems = dct_tbcouponalloweditems

    def migrate_tbCoupons(self):
        """
        :return:
        """
        _logger.info("Migrate tbCoupons")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_k_tbcoupons_v_loyalty_program:
            return
        table_name = f"{self.db_name}.dbo.tbCoupons"
        lst_tbl_tbcoupons = self.dct_tbl.get(table_name)
        lst_tbl_tbCouponAllowedItems = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbCouponAllowedItems"
        )
        model_name = "loyalty.program"

        for i, tbcoupons in enumerate(lst_tbl_tbcoupons):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbcoupons)}"
            obj_id_i = tbcoupons.CouponID
            name = tbcoupons.CouponCode

            lst_associate_item = [
                a
                for a in lst_tbl_tbCouponAllowedItems
                if a.CouponID == obj_id_i
            ]

            if not lst_associate_item:
                continue

            value = {
                "name": name,
                "active": tbcoupons.IsActive,
            }

            obj_coupon_id = env[model_name].create(value)

            self.dct_k_tbcoupons_v_loyalty_program[obj_id_i] = obj_coupon_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

            value_reward = {
                "active": tbcoupons.IsActive,
                "discount": tbcoupons.CouponAmount * 100,
                "program_id": obj_coupon_id.id,
                "discount_mode": "percent"
                if tbcoupons.IsPercent
                else "per_order",
            }
            obj_coupon_reward_id = env["loyalty.reward"].create(value_reward)
            lst_product = []
            for associate_item in lst_associate_item:
                product_id = self.dct_k_tbstoreitems_v_product_template.get(
                    associate_item.StoreItemID
                )
                if product_id:
                    lst_product.append(product_id.id)
                else:
                    msg = f"Missing product id {associate_item.StoreItemID}"
                    _logger.warning(msg)
                    self.lst_warning.append(msg)

            if lst_associate_item and not lst_product:
                msg = f"Coupon id {obj_id_i} has not product associate, it's empty."
                _logger.warning(msg)
                self.lst_warning.append(msg)

            value_rule = {
                "active": tbcoupons.IsActive,
                "program_id": obj_coupon_id.id,
                "product_ids": lst_product,
            }
            if tbcoupons.MinimumAmount:
                value_rule["minimum_amount"] = tbcoupons.MinimumAmount
            obj_coupon_rule_id = env["loyalty.rule"].create(value_rule)
            # TODO tbStoreShoppingCartItemCoupons

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
        model_name = "res.partner"

        for i, tbexpensecategories in enumerate(lst_tbl_tbexpensecategories):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbexpensecategories)}"
            # TODO update variable name from database table
            obj_id_i = tbexpensecategories.ID
            # name = tbexpensecategories.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbexpensecategories[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbgalleryitems in enumerate(lst_tbl_tbgalleryitems):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbgalleryitems)}"
            # TODO update variable name from database table
            obj_id_i = tbgalleryitems.ID
            # name = tbgalleryitems.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbgalleryitems[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbknowledgeanswerchoices in enumerate(
            lst_tbl_tbknowledgeanswerchoices
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbknowledgeanswerchoices)}"
            # TODO update variable name from database table
            obj_id_i = tbknowledgeanswerchoices.ID
            # name = tbknowledgeanswerchoices.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbknowledgeanswerchoices[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

        self.dct_tbknowledgeanswerchoices = dct_tbknowledgeanswerchoices

    def migrate_tbKnowledgeAnswerResults(self):
        """
        :return:
        """
        _logger.info("Migrate tbKnowledgeAnswerResults")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_k_tbknowledgeanswerresults_v_survey_question_answer:
            return
        dct_tbknowledgeanswerresults = {}
        table_name = f"{self.db_name}.dbo.tbKnowledgeAnswerResults"
        lst_tbl_tbknowledgeanswerresults = self.dct_tbl.get(table_name)
        model_name = "res.partner"

        for i, tbknowledgeanswerresults in enumerate(
            lst_tbl_tbknowledgeanswerresults
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbknowledgeanswerresults)}"
            # TODO update variable name from database table
            obj_id_i = tbknowledgeanswerresults.ID
            # name = tbknowledgeanswerresults.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbknowledgeanswerresults[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

        self.dct_k_tbknowledgeanswerresults_v_survey_question_answer = (
            dct_tbknowledgeanswerresults
        )

    def migrate_tbKnowledgeQuestions(self):
        """
        :return:
        """
        _logger.info("Migrate tbKnowledgeQuestions")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_k_tbknowledgequestions_v_survey_question:
            return
        dct_tbknowledgequestions = {}
        table_name = f"{self.db_name}.dbo.tbKnowledgeQuestions"
        lst_tbl_tbknowledgequestions = self.dct_tbl.get(table_name)
        model_name = "res.partner"

        for i, tbknowledgequestions in enumerate(lst_tbl_tbknowledgequestions):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbknowledgequestions)}"
            # TODO update variable name from database table
            obj_id_i = tbknowledgequestions.ID
            # name = tbknowledgequestions.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbknowledgequestions[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

        self.dct_k_tbknowledgequestions_v_survey_question = (
            dct_tbknowledgequestions
        )

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
        model_name = "res.partner"

        for i, tbknowledgetestresults in enumerate(
            lst_tbl_tbknowledgetestresults
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbknowledgetestresults)}"
            # TODO update variable name from database table
            obj_id_i = tbknowledgetestresults.ID
            # name = tbknowledgetestresults.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbknowledgetestresults[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbknowledgetests in enumerate(lst_tbl_tbknowledgetests):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbknowledgetests)}"
            # TODO update variable name from database table
            obj_id_i = tbknowledgetests.ID
            # name = tbknowledgetests.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbknowledgetests[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbmailtemplates in enumerate(lst_tbl_tbmailtemplates):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbmailtemplates)}"
            # TODO update variable name from database table
            obj_id_i = tbmailtemplates.ID
            # name = tbmailtemplates.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbmailtemplates[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

        self.dct_tbmailtemplates = dct_tbmailtemplates

    def migrate_tbStoreCategories(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreCategories")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_k_tbstorecategories_v_product_category:
            return
        table_name = f"{self.db_name}.dbo.tbStoreCategories"
        lst_tbl_tbstorecategories = self.dct_tbl.get(table_name)
        model_name = "product.category"

        for i, tbstorecategories in enumerate(lst_tbl_tbstorecategories):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstorecategories)}"

            # TODO AffiliateLinks
            obj_id_i = tbstorecategories.CategoryID
            name = tbstorecategories.CategoryNameFR

            value = {
                "name": name,
            }

            obj_product_category_id = env[model_name].create(value)

            self.dct_k_tbstorecategories_v_product_category[
                obj_id_i
            ] = obj_product_category_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

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
        model_name = "res.partner"

        for i, tbstoreitemanimators in enumerate(lst_tbl_tbstoreitemanimators):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitemanimators)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitemanimators.ID
            # name = tbstoreitemanimators.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitemanimators[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreitemcontentpackagemappings in enumerate(
            lst_tbl_tbstoreitemcontentpackagemappings
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitemcontentpackagemappings)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitemcontentpackagemappings.ID
            # name = tbstoreitemcontentpackagemappings.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitemcontentpackagemappings[
                obj_id_i
            ] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreitemcontentpackages in enumerate(
            lst_tbl_tbstoreitemcontentpackages
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitemcontentpackages)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitemcontentpackages.ID
            # name = tbstoreitemcontentpackages.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitemcontentpackages[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreitemcontents in enumerate(lst_tbl_tbstoreitemcontents):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitemcontents)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitemcontents.ID
            # name = tbstoreitemcontents.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitemcontents[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreitemcontenttypes in enumerate(
            lst_tbl_tbstoreitemcontenttypes
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitemcontenttypes)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitemcontenttypes.ID
            # name = tbstoreitemcontenttypes.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitemcontenttypes[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreitempictures in enumerate(lst_tbl_tbstoreitempictures):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitempictures)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitempictures.ID
            # name = tbstoreitempictures.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitempictures[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

        self.dct_tbstoreitempictures = dct_tbstoreitempictures

    def migrate_tbStoreItems(self):
        """
        :return:
        """
        _logger.info("Migrate tbStoreItems")
        if self.dct_tbstoreitems:
            return
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        default_user_seller_id = self.dct_res_user_id[DEFAULT_SELL_USER_ID]
        default_seller_id = self.dct_partner_id[DEFAULT_SELL_USER_ID]
        table_name = f"{self.db_name}.dbo.tbStoreItems"
        lst_tbl_tbstoreitems = self.dct_tbl.get(table_name)
        model_name = "event.event"

        for i, tbstoreitems in enumerate(lst_tbl_tbstoreitems):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitems)}"
            obj_id_i = tbstoreitems.ItemID
            # ? ItemOrder
            # ? ItemShippingFee
            # DateCreated
            # ItemSellPrice
            # ItemBuyCost
            # ItemDescriptionFR
            # ItemDescriptionExtentedFR
            if tbstoreitems.CategoryID in (1, 2):
                value_event = {
                    "name": tbstoreitems.ItemNameFR,
                    "user_id": default_user_seller_id.id,
                    "organizer_id": default_seller_id.id,
                    "create_date": tbstoreitems.DateCreated,
                    "date_begin": tbstoreitems.DateCreated,
                    "date_end": tbstoreitems.DateCreated,
                    "date_tz": "America/Montreal",
                    "is_published": tbstoreitems.IsOnHomePage,
                    "active": tbstoreitems.IsActive,
                }
                event_id = env[model_name].create(value_event)
                self.dct_event[obj_id_i] = event_id
                # TODO missing ItemBuyCost
                price = tbstoreitems.ItemSellPrice / 1.14975
                value_event_ticket = {
                    "name": tbstoreitems.ItemNameFR,
                    "event_id": event_id.id,
                    "product_id": env.ref(
                        "event_sale.product_product_event"
                    ).id,
                    "price": price,
                    "create_date": tbstoreitems.DateCreated,
                }
                event_ticket_id = env["event.event.ticket"].create(
                    value_event_ticket
                )
                self.dct_event_ticket[obj_id_i] = event_ticket_id
            else:
                categorie_id = (
                    self.dct_k_tbstorecategories_v_product_category.get(
                        tbstoreitems.CategoryID
                    )
                )
                value_product = {
                    "name": tbstoreitems.ItemNameFR,
                    "list_price": tbstoreitems.ItemSellPrice / 1.14975,
                    "standard_price": tbstoreitems.ItemBuyCost,
                    "create_date": tbstoreitems.DateCreated,
                    "categ_id": categorie_id.id,
                    "is_published": tbstoreitems.IsOnHomePage,
                    "active": tbstoreitems.IsActive,
                }
                product_template_id = env["product.template"].create(
                    value_product
                )
                self.dct_k_tbstoreitems_v_product_template[
                    obj_id_i
                ] = product_template_id

            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{tbstoreitems.ItemNameFR}' id {obj_id_i}"
                )

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
        model_name = "res.partner"

        for i, tbstoreitemtaxes in enumerate(lst_tbl_tbstoreitemtaxes):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitemtaxes)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitemtaxes.ID
            # name = tbstoreitemtaxes.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitemtaxes[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreitemtrainingcourses in enumerate(
            lst_tbl_tbstoreitemtrainingcourses
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitemtrainingcourses)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitemtrainingcourses.ID
            # name = tbstoreitemtrainingcourses.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitemtrainingcourses[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreitemvariants in enumerate(lst_tbl_tbstoreitemvariants):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreitemvariants)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreitemvariants.ID
            # name = tbstoreitemvariants.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreitemvariants[obj_id_i] = obj_res_partner_id
            _logger.info(
                f"{pos_id} - {model_name} - table {table_name} - ADDED"
                f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreshoppingcartitemcoupons in enumerate(
            lst_tbl_tbstoreshoppingcartitemcoupons
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreshoppingcartitemcoupons)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreshoppingcartitemcoupons.ID
            # name = tbstoreshoppingcartitemcoupons.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreshoppingcartitemcoupons[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreshoppingcartitems in enumerate(
            lst_tbl_tbstoreshoppingcartitems
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreshoppingcartitems)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreshoppingcartitems.ID
            # name = tbstoreshoppingcartitems.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreshoppingcartitems[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        model_name = "res.partner"

        for i, tbstoreshoppingcartitemtaxes in enumerate(
            lst_tbl_tbstoreshoppingcartitemtaxes
        ):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreshoppingcartitemtaxes)}"
            # TODO update variable name from database table
            obj_id_i = tbstoreshoppingcartitemtaxes.ID
            # name = tbstoreshoppingcartitemtaxes.Name
            name = ""

            value = {
                "name": name,
            }

            obj_res_partner_id = env[model_name].create(value)

            dct_tbstoreshoppingcartitemtaxes[obj_id_i] = obj_res_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
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
        if self.dct_k_tbstoreshoppingcarts_v_sale_order:
            return
        table_name = f"{self.db_name}.dbo.tbStoreShoppingCarts"
        lst_tbl_tbstoreshoppingcarts = self.dct_tbl.get(table_name)
        lst_tbl_store_shopping_cart_item = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreShoppingCartItems"
        )
        default_account_client_recv_id = env["account.account"].search(
            domain=[("account_type", "=", "asset_receivable")], limit=1
        )
        # Configure journal for cash
        journal_id = env["account.journal"].search(
            domain=[("type", "=", "cash")],
            limit=1,
        )
        journal_sale_id = env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", env.company.id)]
        )[0]
        model_name = "sale.order"

        for i, tbstoreshoppingcarts in enumerate(lst_tbl_tbstoreshoppingcarts):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbstoreshoppingcarts)}"
            obj_id_i = tbstoreshoppingcarts.CartID
            if (
                not tbstoreshoppingcarts.IsCompleted
                and tbstoreshoppingcarts.ProviderStatusText != "completed"
            ):
                continue
            i += 1
            if DEBUG_LIMIT and i > LIMIT:
                continue
            order_partner_id = self.dct_partner_id.get(
                tbstoreshoppingcarts.UserID
            )
            if not order_partner_id:
                # Will force public partner
                order_partner_id = env.ref("base.public_partner")
                # _logger.error(
                #     f"Cannot find client {store_shopping_cart.UserID} into"
                #     f" order {store_shopping_cart.CartID}"
                # )
                # continue
            value_sale_order = {
                # "name": store_shopping_cart.ItemNameFR,
                # "list_price": store_item.ItemSellPrice,
                # "standard_price": store_item.ItemBuyCost,
                "date_order": tbstoreshoppingcarts.DateCreated,
                "create_date": tbstoreshoppingcarts.DateCreated,
                "partner_id": order_partner_id.id,
                # "is_published": store_item.IsActive,
                "state": "done",
            }
            sale_order_id = env[model_name].create(value_sale_order)
            # move.action_post()
            self.dct_k_tbstoreshoppingcarts_v_sale_order[
                tbstoreshoppingcarts.CartID
            ] = sale_order_id
            lst_items = [
                a
                for a in lst_tbl_store_shopping_cart_item
                if a.CartID == tbstoreshoppingcarts.CartID
            ]
            if not lst_items:
                # Create a new one
                # TODO check store_shopping_cart.ProviderStatusText
                # TODO check store_shopping_cart.ProviderTransactionID
                # TODO check store_shopping_cart.TotalAmount
                # TODO check store_shopping_cart.TotalDiscount

                value_sale_order_line = {
                    "name": "Non défini",
                    # "list_price": store_item.ItemSellPrice,
                    # "standard_price": store_item.ItemBuyCost,
                    "create_date": tbstoreshoppingcarts.DateCreated,
                    "order_partner_id": order_partner_id.id,
                    "order_id": sale_order_id.id,
                    "price_unit": tbstoreshoppingcarts.TotalAmount / 1.14975,
                    "product_qty": 1,
                    "display_type": False,
                    "product_id": 1,
                    # "tax_ids":
                    # "is_published": store_item.IsActive,
                }
                sale_order_line_id = env["sale.order.line"].create(
                    value_sale_order_line
                )
                _logger.error(
                    "Need more information, missing charts items for chart"
                    f" {tbstoreshoppingcarts.CartID}"
                )
            else:
                for item in lst_items:
                    product_shopping_id = (
                        self.dct_k_tbstoreitems_v_product_template.get(
                            item.ItemID
                        )
                    )
                    if not product_shopping_id:
                        event_shopping_id = self.dct_event.get(item.ItemID)
                        event_ticket_shopping_id = self.dct_event_ticket.get(
                            item.ItemID
                        )
                        product_shopping_id = env.ref(
                            "event_sale.product_product_event"
                        )
                        if not event_shopping_id:
                            _logger.error(
                                f"Cannot find product id {item.ItemID}"
                            )
                            continue
                        name = "ticket"

                        value_event_registration = {
                            "event_id": event_shopping_id.id,
                            "event_ticket_id": event_ticket_shopping_id.id,
                            "partner_id": order_partner_id.id,
                        }
                        # TODO state change open to done when event is done
                        event_registration_id = env[
                            "event.registration"
                        ].create(value_event_registration)
                    else:
                        name = product_shopping_id.name
                    value_sale_order_line = {
                        "name": name,
                        # "list_price": store_item.ItemSellPrice,
                        # "standard_price": store_item.ItemBuyCost,
                        "create_date": tbstoreshoppingcarts.DateCreated,
                        "order_partner_id": order_partner_id.id,
                        "order_id": sale_order_id.id,
                        "price_unit": item.ItemSellPrice / 1.14975,
                        "product_qty": item.Quantity,
                        "product_id": product_shopping_id.id,
                        # "is_published": store_item.IsActive,
                    }
                    sale_order_line_id = env["sale.order.line"].create(
                        value_sale_order_line
                    )
            # Create invoice
            # Validate sale order
            # sale_order_id.action_confirm()
            if MIGRATE_INVOICE:
                # Create Invoice
                invoice_vals = {
                    "move_type": "out_invoice",  # for customer invoice
                    "partner_id": sale_order_id.partner_id.id,
                    "journal_id": journal_sale_id.id,
                    "date": tbstoreshoppingcarts.DateCreated,
                    "invoice_date": tbstoreshoppingcarts.DateCreated,
                    "invoice_origin": sale_order_id.name,
                    "currency_id": env.company.currency_id.id,
                    "company_id": env.company.id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": line.product_id.id,
                                "name": line.name,
                                "quantity": line.product_uom_qty,
                                "price_unit": line.price_unit,
                                "account_id": env.ref(
                                    "l10n_ca.ca_en_chart_template_en"
                                ).id,
                                # "tax_ids": False,
                            },
                        )
                        for line in sale_order_id.order_line
                    ],
                }

                invoice_id = env["account.move"].create(invoice_vals)
                invoice_id.action_post()

                # Validate Invoice (optional)
                # sale_order_id.write({"invoice_ids": [(4, invoice_id.id)]})
                if invoice_id.amount_total > 0:
                    vals = {
                        "amount": invoice_id.amount_total,
                        "date": tbstoreshoppingcarts.DateCreated,
                        "partner_type": "customer",
                        "partner_id": sale_order_id.partner_id.id,
                        "payment_type": "inbound",
                        "payment_method_id": env.ref(
                            "account.account_payment_method_manual_in"
                        ).id,
                        "journal_id": journal_id.id,
                        "currency_id": env.company.currency_id.id,
                        "company_id": env.company.id,
                    }
                    payment_id = env["account.payment"].create(vals)
                    # invoice_id.write({"payment_id": payment_id.id})
                    payment_id.action_post()
                    payment_ml = payment_id.line_ids.filtered(
                        lambda l: l.account_id
                        == default_account_client_recv_id
                    )
                    res = invoice_id.with_context(
                        move_id=invoice_id.id,
                        line_id=payment_ml.id,
                        paid_amount=invoice_id.amount_total,
                    ).js_assign_outstanding_line(payment_ml.id)
                    if not payment_ml.reconciled:
                        _logger.warning(
                            f"Facture non payé id %s" % invoice_id.id
                        )
                    # partials = res.get("partials")
                    # if partials:
                    #     print(partials)
                    #     invoice_id.with_context(
                    #         paid_amount=invoice_id.amount_total
                    #     ).js_assign_outstanding_line(payment_ml.id)
                    # print(payment_ml.reconciled)
                    # print(invoice_id.amount_residual)
                    # print(invoice_id.payment_state)
                # invoice_id.action_post()
                # invoice_id.js_assign_outstanding_line(payment_id.id)
                # invoice_id._post()

                # Create invoice
                # new_invoice = sale_order_id._create_invoices()
                # Validate invoice
                # new_invoice.action_post()
                # new_invoice.invoice_origin = sale_order_id.name + ", 987 - " + self.name
                # invoice = sale_order_id.invoice_ids

            name = ""
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

    def migrate_tbTrainingCourses(self):
        """
        :return:
        """
        _logger.info("Migrate tbTrainingCourses")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_k_tbtrainingcourses_v_slide_channel:
            return
        table_name = f"{self.db_name}.dbo.tbTrainingCourses"
        lst_tbl_tbtrainingcourses = self.dct_tbl.get(table_name)
        model_name = "slide.channel"

        default_seller_id = self.dct_partner_id[DEFAULT_SELL_USER_ID]
        default_seller_id.seller = True
        default_seller_id.url_handler = default_seller_id.name.replace(
            " ", "_"
        )
        default_user_seller_id = self.dct_res_user_id[DEFAULT_SELL_USER_ID]

        for i, tbtrainingcourses in enumerate(lst_tbl_tbtrainingcourses):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbtrainingcourses)}"

            # Slide Channel
            # TODO Duration -> create a statistics, check _compute_slides_statistics
            # Ignore CourseID
            # TODO ReleaseDate
            obj_id_i = tbtrainingcourses.TestID
            name = tbtrainingcourses.CourseName

            value = {
                "name": name,
                # "description": slide_channel.Description.strip(),
                "is_published": True,
                "visibility": "public",
                "enroll": "payment",
                "create_date": tbtrainingcourses.CreatedDate,
                "seller_id": default_seller_id.id,
                "user_id": default_user_seller_id.id,
            }

            obj_slide_channel_id = env[model_name].create(value)

            self.dct_k_tbtrainingcourses_v_slide_channel[
                obj_id_i
            ] = obj_slide_channel_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' id {obj_id_i}"
                )

    def continue_migrate_tbTrainingCourses_knowledge_question(
        self, obj_slide_channel_id, test_id_tbl
    ):
        default_user_seller_id = self.dct_res_user_id[DEFAULT_SELL_USER_ID]
        env = api.Environment(self.cr, SUPERUSER_ID, {})

        lbl_knowledge_test = f"{self.db_name}.dbo.tbKnowledgeTests"
        lst_tbl_knowledge_test = self.dct_tbl.get(lbl_knowledge_test)
        lst_knowledge_test_tbl = [
            a for a in lst_tbl_knowledge_test if a.TestID == test_id_tbl
        ]
        if not lst_knowledge_test_tbl:
            msg = f"About tbKnowledgeTests, missing TestID {test_id_tbl}"
            _logger.warning(msg)
            self.lst_warning.append(msg)
            return False, False
        knowledge_test_tbl = lst_knowledge_test_tbl[0]

        obj_slide_channel_id.description = knowledge_test_tbl.CertificateBodyFR

        # Survey.question init
        lbl_knowledge_question = f"{self.db_name}.dbo.tbKnowledgeQuestions"
        lst_tbl_knowledge_question = self.dct_tbl.get(lbl_knowledge_question)
        lst_knowledge_question_tbl = [
            a for a in lst_tbl_knowledge_question if a.TestID == test_id_tbl
        ]
        if not lst_knowledge_question_tbl:
            msg = f"About tbKnowledgeQuestions, missing TestID {test_id_tbl}"
            _logger.warning(msg)
            self.lst_warning.append(msg)
            return False, False

        # Survey.question.answer init
        lbl_knowledge_question_answer = (
            f"{self.db_name}.dbo.tbKnowledgeAnswerChoices"
        )
        lst_tbl_knowledge_question_answer = self.dct_tbl.get(
            lbl_knowledge_question_answer
        )

        # Survey.survey create
        # TODO if enable certification_give_badge, need to create gamification.badge and associate to certification_badge_id
        value_survey_survey = {
            "title": knowledge_test_tbl.TestName,
            "certification": True,
            # "certification_give_badge": True,
            "scoring_type": "scoring_with_answers",
            "user_id": default_user_seller_id.id,
        }
        obj_survey = env["survey.survey"].create(value_survey_survey)
        self.dct_k_knowledgetest_v_survey_id[
            knowledge_test_tbl.TestID
        ] = obj_survey

        for knowledge_question_tbl in lst_knowledge_question_tbl:
            # ignore EN like QuestionEN and SubjectEN
            # TODO SubjectFR
            base_qvalues = {
                "sequence": knowledge_question_tbl.QuestionOrder + 9,
                "title": knowledge_question_tbl.QuestionFR,
                "survey_id": obj_survey.id,
            }
            if knowledge_question_tbl.SubjectFR:
                base_qvalues[
                    "description"
                ] = f"<p>{knowledge_question_tbl.SubjectFR}</p>"
            question_id = env["survey.question"].create(base_qvalues)
            self.dct_k_tbknowledgequestions_v_survey_question[
                knowledge_question_tbl.QuestionID
            ] = question_id

            # Continue Survey.question.answer
            tbl_knowledge_question_id = knowledge_question_tbl.QuestionID
            lst_knowledge_question_answer_tbl = [
                a
                for a in lst_tbl_knowledge_question_answer
                if a.QuestionID == tbl_knowledge_question_id
            ]
            if not lst_knowledge_question_answer_tbl:
                msg = (
                    "About tbKnowledgeAnswerChoices, missing"
                    f" QuestionID {tbl_knowledge_question_id}"
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
                continue
            # TODO AnswerEN
            for (
                knowledge_question_answer_tbl
            ) in lst_knowledge_question_answer_tbl:
                sequence = knowledge_question_answer_tbl.AnswerOrder + 9
                value_answer = {
                    "sequence": sequence,
                    "value": knowledge_question_answer_tbl.AnswerFR,
                    "is_correct": knowledge_question_answer_tbl.IsRightAnswer,
                    "question_id": question_id.id,
                    "answer_score": 10
                    if knowledge_question_answer_tbl.IsRightAnswer
                    else 0,
                }
                question_answer_id = env["survey.question.answer"].create(
                    value_answer
                )
                self.dct_k_tbknowledgeanswerresults_v_survey_question_answer[
                    knowledge_question_answer_tbl.AnswerID
                ] = question_answer_id
        return obj_survey, knowledge_test_tbl

    def continue_migrate_tbTrainingCourses_slide_slide(
        self,
        knowledge_test_tbl,
        obj_slide_channel_id,
        obj_survey,
    ):
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        default_user_seller_id = self.dct_res_user_id[DEFAULT_SELL_USER_ID]

        # Create slide.slide
        ticks = knowledge_test_tbl.TrainingDuration
        td = datetime.timedelta(microseconds=ticks / 10)
        days, hours, minutes = (
            td.days,
            td.seconds // 3600,
            td.seconds % 3600 / 60.0,
        )
        time_duration_hour = hours

        # TODO Subject
        # TODO TestKey ??
        # TODO Trainer - abandon, do it manually
        # is compute later PassingGrade
        value_slide = {
            "name": knowledge_test_tbl.TestName,
            "channel_id": obj_slide_channel_id.id,
            "slide_category": "certification",
            "slide_type": "certification",
            "description": knowledge_test_tbl.CertificateBodyFR,
            "survey_id": obj_survey.id,
            "is_published": True,
            "website_published": True,
            "completion_time": time_duration_hour,
            "create_date": knowledge_test_tbl.DateCreated,
            "user_id": default_user_seller_id.id,
        }
        obj_slide = env["slide.slide"].create(value_slide)
        self.dct_k_survey_v_slide_survey_id[obj_survey.id] = obj_slide
        return obj_slide

    def continue_migrate_tbTrainingCourses_knownledge_answer(self):
        env = api.Environment(self.cr, SUPERUSER_ID, {})

        lst_tbl_knowledge_test_results = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbKnowledgeTestResults"
        )
        # Import result survey
        for tbl_knowledge_test_results in lst_tbl_knowledge_test_results:
            partner_id = self.dct_partner_id.get(
                tbl_knowledge_test_results.UserID
            )
            if not partner_id:
                msg = (
                    "Cannot find partner_id for UserID"
                    f" '{tbl_knowledge_test_results.UserID}'"
                )
                _logger.error(msg)
                self.lst_error.append(msg)
                continue

            obj_survey = self.dct_k_knowledgetest_v_survey_id.get(
                tbl_knowledge_test_results.TestID
            )
            if not obj_survey:
                msg = (
                    "Cannot find survey for TestID"
                    f" '{tbl_knowledge_test_results.TestID}'"
                )
                _logger.error(msg)
                self.lst_error.append(msg)
                continue
            # DONE Ignore Grade, will be recalcul, validate the value is good by a warning
            # DONE validate IsSuccessful
            # TODO start date and end date is the same
            # DONE last_displayed_page_id select last question id
            obj_slide = self.dct_k_survey_v_slide_survey_id[obj_survey.id]

            # Create partner input survey
            value_survey_user_input = {
                "survey_id": obj_survey.id,
                "create_date": tbl_knowledge_test_results.DateCreated,
                "start_datetime": tbl_knowledge_test_results.DateCreated,
                "end_datetime": tbl_knowledge_test_results.DateCreated,
                "state": "done",
                "email": partner_id.email,
                "nickname": partner_id.name,
                "partner_id": partner_id.id,
                # "last_displayed_page_id": 1,
                "slide_id": obj_slide.id,
            }
            obj_survey_user_input = env["survey.user_input"].create(
                value_survey_user_input
            )
            lst_tbl_knowledge_answer_results = self.dct_tbl.get(
                f"{self.db_name}.dbo.tbKnowledgeAnswerResults"
            )
            # Get associate result line
            lst_associate_answer_result = [
                a
                for a in lst_tbl_knowledge_answer_results
                if a.TestResultID == tbl_knowledge_test_results.TestResultID
            ]
            survey_question_answer = None
            obj_survey_user_input_line = None
            for associate_answer_result in lst_associate_answer_result:
                try:
                    survey_question_answer = self.dct_k_tbknowledgeanswerresults_v_survey_question_answer[
                        associate_answer_result.AnswerID
                    ]
                except Exception as e:
                    msg = (
                        "Cannot retreive answer ID"
                        f" {associate_answer_result.AnswerID} for"
                        " survey_question_answer."
                    )
                    _logger.error(msg)
                    self.lst_error.append(msg)
                    continue
                value_survey_user_input_line = {
                    "user_input_id": obj_survey_user_input.id,
                    "question_id": survey_question_answer.question_id.id,
                    "answer_type": "suggestion",
                    "create_date": tbl_knowledge_test_results.DateCreated,
                    "suggested_answer_id": survey_question_answer.id,
                    "answer_is_correct": survey_question_answer.is_correct,
                    "answer_score": 10
                    if survey_question_answer.is_correct
                    else 0,
                }
                obj_survey_user_input_line = env[
                    "survey.user_input.line"
                ].create(value_survey_user_input_line)
            # Save last question answered
            if (
                survey_question_answer is not None
                and obj_survey_user_input_line is not None
            ):
                obj_survey_user_input.last_displayed_page_id = (
                    survey_question_answer.question_id.id
                )
            # Fill channel partner to show certification complete
            completed = obj_survey_user_input.scoring_success
            value_slide_channel_partner = {
                "channel_id": obj_slide.channel_id.id,
                "completion": 100 if completed else 0,
                "completed_slides_count": 1 if completed else 0,
                "completed": completed,
                "partner_id": partner_id.id,
                "create_date": tbl_knowledge_test_results.DateCreated,
            }
            # Validate if exist
            obj_slide_channel_partner = env["slide.channel.partner"].search(
                [
                    ("partner_id", "=", partner_id.id),
                    ("channel_id", "=", obj_slide.channel_id.id),
                ],
                limit=1,
            )
            if obj_slide_channel_partner:
                if obj_slide_channel_partner.completion != 100 and completed:
                    obj_slide_channel_partner.completion = 100
                    # _logger.info(
                    #     "Increase value complete to 100 for partner id"
                    #     f" {partner_id.id}"
                    # )
                # else:
                #     obj_slide_channel_partner.completion = 0
            else:
                obj_slide_channel_partner = env[
                    "slide.channel.partner"
                ].create(value_slide_channel_partner)

            # Create slide.slide.partner
            # Validate if exist
            obj_slide_partner = env["slide.slide.partner"].search(
                [
                    ("partner_id", "=", partner_id.id),
                    ("slide_id", "=", obj_slide.id),
                ],
                limit=1,
            )
            if not obj_slide_partner:
                value_slide_partner = {
                    "create_date": tbl_knowledge_test_results.DateCreated,
                    "slide_id": obj_slide.id,
                    "partner_id": partner_id.id,
                    "completed": completed,
                }
                obj_slide_partner = env["slide.slide.partner"].create(
                    value_slide_partner
                )
            else:
                if not obj_slide_partner.completed and completed:
                    obj_slide_partner.completed = True

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
        mailing_list_id = env.ref("mass_mailing.mailing_list_data")
        model_name = "res.partner"

        for i, tbusers in enumerate(lst_tbl_tbusers):
            if DEBUG_LIMIT and i > LIMIT:
                break

            pos_id = f"{i}/{len(lst_tbl_tbusers)}"

            # Ignore user
            if tbusers.UserID == 1231:
                continue

            obj_id_i = tbusers.UserID
            name = tbusers.FullName
            email = tbusers.Email.lower().strip()
            user_name = tbusers.UserName.lower().strip()

            if email != user_name:
                msg = (
                    f"User name '{user_name}' is different from email"
                    f" '{email}'"
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            if not user_name:
                msg = f"Missing user name for membre {tbusers}"
                _logger.error(msg)
                self.lst_error.append(msg)

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

            obj_partner_id = env[model_name].create(value)
            dct_tbusers[obj_id_i] = obj_partner_id
            self.dct_partner_id[obj_id_i] = obj_partner_id
            if DEBUG_OUTPUT:
                _logger.info(
                    f"{pos_id} - {model_name} - table {table_name} - ADDED"
                    f" '{name}' '{email}' id {obj_id_i}"
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

            if obj_id_i == DEFAULT_SELL_USER_ID:
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

                self.dct_res_user_id[obj_id_i] = obj_user

        self.dct_tbusers = dct_tbusers
