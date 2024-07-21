# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import collections
import datetime
import logging
import os
import pickle

import unidecode

from odoo import SUPERUSER_ID, _, api, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# TODO don't forget to increase memory
# --limit-memory-soft=8589934592 --limit-memory-hard=10737418240

HOST = "localhost"
USER = ""
PASSWD = ""
DB_NAME = ""
DEFAULT_SELL_USER_ID = 2  # or 8

try:
    import pymssql

    assert pymssql
except ImportError:
    raise ValidationError(
        'pymssql not available. Please install "pymssql" python package.'
    )

if not HOST or not USER or not PASSWD or not DB_NAME:
    raise ValidationError(
        f"Please, fill constant HOST/USER/PASSWD/DB_NAME into files {__file__}"
    )

# TODO update me with your backup version
BACKUP_PATH = "/tmp/"
FILE_PATH = f"{BACKUP_PATH}/document/doc"
SECRET_PASSWORD = ""
DEBUG_LIMIT = False
LIMIT = 20
FORCE_ADD_USER_EMAIL = ""
GENERIC_EMAIL = f"%s_membre@exemple.ca"
ENABLE_TIER_VALIDATION = True
DISABLE_CREATE_USER = False
MINIMUM_IMPORT = False


def post_init_hook(cr, e):
    _logger.info("Start migration clienta.")
    migration = Migration(cr)

    # General configuration
    # migration.setup_configuration()

    # Create warehouse
    # migration.set_head_quarter()

    # Create company
    # migration.migrate_company()

    # Update user configuration
    # migration.update_user(dry_run=False)

    # Create file
    # if not MINIMUM_IMPORT:
    #     migration.migrate_muk_dms()

    # Create user
    migration.migrate_member()

    # Create product category
    migration.migrate_product_category()

    # Create slide channel
    migration.migrate_slide_channel()

    # TODO à changer

    # Print email
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

    # Print summary
    env = api.Environment(cr, SUPERUSER_ID, {})
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
    ]
    print(f"Migrate into {len(lst_model)} models.")
    for model in lst_model:
        print(f"{len(env[model].search([]))} {model}")


class Struct(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


class Migration:
    def __init__(self, cr):
        assert pymssql
        self.host = HOST
        self.user = USER
        self.passwd = PASSWD
        self.db_name = DB_NAME
        self.conn = pymssql.connect(
            server=self.host,
            user=self.user,
            port="1433",
            password=self.passwd,
            database=self.db_name,
            # charset="utf8",
            # use_unicode=True,
        )
        # Path of the backup
        self.source_code_path = BACKUP_PATH
        self.logo_path = f"{self.source_code_path}/images/logo"
        self.cr = cr

        self.head_quarter = None

        self.dct_companie = {}
        self.dct_tbl_companie = {}
        self.dct_companie_companie = {}
        self.dct_companie_point_service = {}
        # self.dct_companie_by_email = {}
        self.dct_pointservice = {}
        self.dct_fichier = {}
        self.dct_produit = {}
        self.dct_membre = {}
        self.dct_res_user = {}
        self.dct_survey_question_answer = {}
        self.dct_survey = {}
        self.dct_slide_survey_id = {}
        self.dct_product_template = {}
        self.dct_event = {}
        self.dct_event_ticket = {}
        self.dct_sale_order = {}
        self.dct_question = {}
        self.dct_partner = {}
        self.dct_companie_membre = {}
        self.dct_categorie_sous_categorie = {}
        self.dct_slide_channel = {}
        self.dct_product_category = {}
        self.dct_demande_service = {}
        self.dct_offre_service = {}
        self.dct_echange_service = {}

        self.lst_generic_email = []
        self.lst_used_email = []

        self.lst_error = []
        self.lst_warning = []

        self.dct_tbl = self._fill_tbl()

    def set_head_quarter(self):
        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            self.head_quarter = env["res.company"].browse(1)

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

        dct_tbl = {
            f"{a[0]}.{a[1]}.{a[2]}": []
            for a in tpl_result
            if a[2].startswith("tb")
        }
        dct_short_tbl = {
            f"{a[0]}.{a[1]}.{a[2]}": a[2]
            for a in tpl_result
            if a[2].startswith("tb")
        }

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

            # if not SECRET_PASSWORD:
            #     raise Exception(
            #         "SECRET_PASSWORD is empty, fill it (search $password into"
            #         " database of companie)"
            #     )

            # if table == "tbl_membre":
            #     str_query = f"""SELECT *,DECODE(MotDePasse,'{SECRET_PASSWORD}') AS MotDePasseRaw FROM tbl_membre;"""
            #     lst_column_name.append("MotDePasseRaw")
            # else:
            #     str_query = f"""SELECT * FROM {table};"""
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

        # return Struct(**dct_tbl)
        return dct_tbl

    def setup_configuration(self, dry_run=False):
        _logger.info("Setup configuration")

        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})
            # CRM
            # team = env['crm.team'].browse(1)
            # Team name Europe need to be change in i18n french canadian
            # team.name = "Québec"

            # General configuration
            values = {
                # 'use_quotation_validity_days': True,
                # 'quotation_validity_days': 30,
                # 'portal_confirmation_sign': True,
                # 'portal_invoice_confirmation_sign': True,
                # 'group_sale_delivery_address': True,
                # 'group_sale_order_template': True,
                # 'default_sale_order_template_id': True,
                # 'use_sale_note': True,
                # 'sale_note': "N° TPS : \n"
                #              "N° TVQ : \n"
                #              "N° RBQ : 5775-6991-01\n"
                #              "N° BSP : SC 20047464\n"
                #              "Des frais de 2% par mois sont exigés sur tout solde impayé"
                #              " après la date d'échéance.",
                # 'refund_total_tip_amount_included_to_employee': True,
                # 'group_discount_per_so_line': True,
                # 'group_use_lead': True,
                # 'generate_lead_from_alias': True,
                # 'crm_alias_prefix': "service",
                "theme_color_brand": "#004a98",
                # 'theme_color_primary': "#2CD5C4",
                "theme_background_image": env.ref(
                    "companie_migrate_mysql.theme_background_image"
                ).datas,
                # 'branding_color_text': "#4c4c4c",
                # Enable multi company for each companie
                "group_multi_company": True,
                "company_share_partner": False,
                "company_share_product": False,
                # Ignore KPI digest
                "digest_emails": False,
                # Authentication
                "auth_signup_reset_password": True,
                # Commercial
                # TODO Cause bug when uninstall, need to do it manually
                # 'module_web_unsplash': False,
                # 'module_partner_autocomplete': False,
            }
            if not dry_run:
                event_config = env["res.config.settings"].sudo().create(values)
                event_config.execute()

    def update_user(self, dry_run=False):
        _logger.info("Update user preference")
        with api.Environment.manage():
            env = api.Environment(self.cr, SUPERUSER_ID, {})

            administrator = env["res.users"].browse(2)
            # administrator.email = "admin@nuagelibre.ca"
            # Add all society to administrator
            administrator.company_ids = env["res.company"].search([]).ids

    def migrate_muk_dms(self):
        """
        Depend on company.
        :return:
        """
        _logger.info("Migrate files")
        # tbl_type_fichier and tbl_fichier

        if not self.dct_fichier:
            # Setup type fichier
            dct_type_fichier = {}
            with api.Environment.manage():
                env = api.Environment(self.cr, SUPERUSER_ID, {})

                i = 0
                for fichier in self.dct_tbl.tbl_type_fichier:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_type_fichier)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    name = fichier.TypeFichier
                    value = {
                        "name": name,
                        "create_date": fichier.DateMAJ_TypeFichier,
                    }

                    category_id = env["muk_dms.category"].create(value)
                    # try:
                    #     category_id = env["muk_dms.category"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    dct_type_fichier[fichier.Id_TypeFichier] = category_id
                    _logger.info(
                        f"{pos_id} - muk_dms.category - tbl_type_fichier -"
                        f" ADDED '{name}' id {fichier.Id_TypeFichier}"
                    )

                # Setup directory
                dct_storage = {}
                i = 0

                # for companie in list(self.dct_pointservice.values()) + list(self.dct_companie.values()):
                for companie in list(self.dct_companie.values()):
                    i += 1
                    pos_id = f"{i}/{len(self.dct_companie.values())}"
                    name = companie.name

                    value = {
                        "name": name,
                        "company": companie.id,
                    }

                    storage_id = env["muk_dms.storage"].create(value)
                    # try:
                    #     storage_id = env["muk_dms.storage"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue

                    if "/" in name:
                        name = name.replace("/", "_")
                    value = {
                        "name": name,
                        "root_storage": storage_id.id,
                        "is_root_directory": True,
                    }

                    directory_id = env["muk_dms.directory"].create(value)
                    # try:
                    #     directory_id = env["muk_dms.directory"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    if companie.id in dct_storage:
                        raise Exception(
                            f"Duplicate {companie} : {dct_storage}"
                        )

                    dct_storage[companie.id] = directory_id
                    _logger.info(
                        f"{pos_id} - muk_dms.storage - tbl_companie - ADDED"
                        f" '{name}' id {storage_id.id if storage_id else ''}"
                    )

                i = 0
                for fichier in self.dct_tbl.tbl_fichier:
                    i += 1
                    pos_id = f"{i}/{len(self.dct_tbl.tbl_fichier)}"

                    if DEBUG_LIMIT and i > LIMIT:
                        break

                    name = fichier.NomFichierOriginal

                    data = open(
                        f"{FILE_PATH}/{fichier.NomFichierStokage}", "rb"
                    ).read()
                    content = base64.b64encode(data)

                    # _, directory_id = self._get_storage(id_companie=result[2])

                    # type_fichier_id, _ = self._get_type_fichier(id_type_fichier=result[1])

                    category = dct_type_fichier.get(fichier.Id_TypeFichier).id

                    value = {
                        "name": name,
                        "category": category,
                        "active": fichier.Si_Disponible == 1,
                        "directory": dct_storage[
                            self.dct_companie.get(fichier.Nocompanie).id
                        ].id,
                        "content": content,
                        "create_date": fichier.DateMAJ_Fichier,
                    }

                    try:
                        file_id = env["muk_dms.file"].create(value)
                    except Exception as e:
                        self.lst_error.append(e)
                        _logger.error(e)
                        continue
                    # Validate not duplicate
                    # files_id = env['muk_dms.file'].search([('name', '=', name), ('directory', '=', directory_id.id)])
                    # if not files_id:
                    #     file_id = env['muk_dms.file'].create(value)
                    # else:
                    #     if len(files_id) > 1:
                    #         raise Exception(f"ERROR, duplicate file id {i}")
                    #     if files_id[0].content == content:
                    #         _logger.info(f"{pos_id} - muk_dms.file - tbl_fichier - SKIPPED DUPLICATED SAME CONTENT '{name}' "
                    #               f"on storage '{directory_id.name}' id {fichier.Id_Fichier}")
                    #     else:
                    #         raise Exception(
                    #             f"ERROR, duplicate file id {i}, content is different, but same name '{name}'")

                    self.dct_fichier[fichier.Id_Fichier] = file_id
                    _logger.info(
                        f"{pos_id} - muk_dms.file - tbl_fichier - ADDED"
                        f" '{name}' on storage"
                        f" '{directory_id.name if directory_id else ''}' id"
                        f" {fichier.Id_Fichier}"
                    )

    def migrate_member(self):
        """
        :return:
        """
        _logger.info("Migrate member")
        # tbl_membre

        # dct_debug_login = self._check_duplicate(
        #     self.dct_tbl.tbl_membre, "NomUtilisateur", verbose=False
        # )
        # dct_debug_email = self._check_duplicate(
        #     self.dct_tbl.tbl_membre, "Courriel", verbose=False
        # )
        # self.dct_tbl["tbl_membre|conflict"] = dct_debug
        # _logger.info("profile")
        # _logger.info(dct_debug_login)
        # _logger.info("email")
        # _logger.info(dct_debug_email)
        nb_membre_int = 0
        nb_membre_ext = 0
        nb_admin = 0

        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if not self.dct_membre:
            dct_membre = {}
            dct_partner = {}
            dct_companie_membre = {}

            i = 0
            tbUsersTab = f"{self.db_name}.dbo.tbUsers"
            dct_tbl_membre = self.dct_tbl.get(tbUsersTab)
            for membre in dct_tbl_membre:
                i += 1
                pos_id = f"{i}/{len(dct_tbl_membre)}"

                email = membre.Email.lower().strip()
                user_name = membre.UserName.lower().strip()

                if email != user_name:
                    _logger.warning(
                        f"User name '{user_name}' is different from email"
                        f" '{email}'"
                    )
                if not user_name:
                    _logger.error(f"Missing user name for membre {membre}")

                # if DEBUG_LIMIT and i > LIMIT:
                #     # except for FORCE_ADD_USER_EMAIL
                #     if FORCE_ADD_USER_EMAIL:
                #         if FORCE_ADD_USER_EMAIL.lower() != email:
                #             continue
                #     else:
                #         break

                # associate_point_service = None
                # if membre.EstUnPointService:
                #     associate_point_service = self.dct_pointservice.get(
                #         membre.NoPointService
                #     ).partner_id

                # login = membre.NomUtilisateur
                # # Get the name in 1 field
                # if membre.Prenom and membre.Nom:
                #     name = f"{membre.Prenom.strip()} {membre.Nom.strip()}"
                # elif membre.Prenom:
                #     name = f"{membre.Prenom.strip()}"
                # elif membre.Nom:
                #     name = f"{membre.Nom.strip()}"
                # else:
                #     name = ""
                #
                # if not associate_point_service and (not login or not name):
                #     msg = (
                #         f"{pos_id} - res.partner - tbl_membre - SKIPPED"
                #         f" EMPTY LOGIN '{name}' id {membre.NoMembre}"
                #     )
                #     _logger.warning(msg)
                #     self.lst_warning.append(msg)
                #     # lst_result .append((None, result))
                #     continue

                # Ignore test user
                # if ("test" in name or "test" in login) and login not in [
                #     "claudettestlaur"
                # ]:
                #     msg = (
                #         f"{pos_id} - res.partner - tbl_membre - SKIPPED"
                #         f" TEST LOGIN name '{name}' login '{login}' id"
                #         f" {membre.NoMembre}"
                #     )
                #     _logger.warning(msg)
                #     self.lst_warning.append(msg)
                #     continue

                create_new_email = not email or email in self.lst_used_email

                associate_point_service = False

                if create_new_email:
                    # Ignore duplicate login, create a new email
                    # if login in dct_debug_login.keys():
                    #     # TODO Need to merge it
                    #     msg = (
                    #         f"{pos_id} - res.partner - tbl_membre -"
                    #         f" SKIPPED DUPLICATED LOGIN name '{name}'"
                    #         f" login '{login}' email '{email}' id"
                    #         f" {membre.NoMembre}"
                    #     )
                    #     _logger.warning(msg)
                    #     self.lst_warning.append(msg)
                    #     continue
                    # Need an email for login, force create it
                    # email = GENERIC_EMAIL % i
                    email = unidecode.unidecode(
                        (GENERIC_EMAIL % user_name)
                        .lower()
                        .strip()
                        .replace(" ", "_")
                    )
                    nb_same_email = self.lst_generic_email.count(email)
                    if nb_same_email > 0:
                        email = unidecode.unidecode(
                            (
                                GENERIC_EMAIL
                                % f"{user_name}_{nb_same_email + 1}"
                            )
                            .lower()
                            .strip()
                            .replace(" ", "_")
                        )
                    self.lst_generic_email.append(email)
                    msg = f"Create generic email '{email}'"
                    _logger.warning(msg)
                    self.lst_warning.append(msg)
                # elif email in dct_debug_email.keys():
                #     # TODO merge user
                #     msg = (
                #         f"{pos_id} - res.partner - tbl_membre - SKIPPED"
                #         f" DUPLICATED EMAIL name '{name}' login '{login}'"
                #         f" email '{email}' id {membre.NoMembre}"
                #     )
                #     _logger.warning(msg)
                #     self.lst_warning.append(msg)
                #     continue

                # if not associate_point_service:
                #     self.lst_used_email.append(email)

                # Show duplicate profile
                # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_login.items())[:15] for a in va[1] if a[37] == -1])
                # Show duplicate email
                # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1]])
                # Show duplicate not empty email
                # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[29].strip() != ""])
                # Show duplicate not empty email actif
                # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[29].strip() != "" and a[37] == -1])
                # Show duplicate email active user
                # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[37] == -1])
                # duplicate email and duplicate user and active
                # '\n'.join([str([f"user '{a[44]}'", f"actif '{a[37]}'", f"acc '{a[2]}'", f"id '{a[0]}'", f"mail '{a[29]}'"]) for va in list(dct_debug_email.items())[:15] for a in va[1] if a[37] == -1 and a[44] in dct_debug_login])

                # Technique remplacé par l'utilisation du courriel
                # if login in dct_debug_login.keys():
                #     # Validate unique email
                #     _logger.info(f"{pos_id} - res.partner - tbl_membre - SKIPPED DUPLICATED "
                #           f"name '{name}' login '{login}' id {result[0]}")
                #
                #     if email in dct_debug_email:
                #         _logger.info(dct_debug_email[email])
                #     continue

                # company_id = self.dct_companie.get(membre.Nocompanie)
                # companie_companie_id = (
                #     self.dct_companie_companie.get(membre.Nocompanie)
                # )
                # companie_point_service_id = (
                #     self.dct_companie_point_service.get(
                #         membre.NoPointService
                #     )
                # )
                # companie_companie_transfer_de_id = (
                #     self.dct_companie_companie.get(membre.TransfereDe)
                # )
                # city_name = self._get_ville(membre.NoVille)
                if not associate_point_service:
                    # TODO IsAnimator is internal member, else only portal member
                    # TODO support CountryID, ProvinceID
                    # TODO support newsletter with ReceiveNewsletter
                    # TODO support DateOfBirth
                    # TODO show lastUpdate migration note field LastUpdatedDate + CreatedDate
                    # Info ignore DisplayName, FirstName, Gender, ProperName, LastName, ProviderUserKey, UserId
                    # TODO Occupation if exist
                    value = {
                        "name": membre.FullName,
                        "email": email,
                        # "supplier": False,
                        # "customer": True,
                        "state_id": 543,  # Quebec
                        "country_id": 38,  # Canada
                        "tz": "America/Montreal",
                        # "active": membre.MembreActif,
                        # "company_id": company_id.id,
                        "create_date": membre.CreatedDate,
                        # "free_member": True,
                    }

                    if membre.AddressLine1 and membre.AddressLine1.strip():
                        value["street"] = membre.AddressLine1.strip()
                    if membre.AddressLine2 and membre.AddressLine2.strip():
                        value["street2"] = membre.AddressLine2.strip()
                    if membre.PostalCode and membre.PostalCode.strip():
                        value["zip"] = membre.PostalCode.strip()
                    if membre.City and membre.City.strip():
                        value["city"] = membre.City.strip()
                    if membre.WebSite and membre.WebSite.strip():
                        value["website"] = membre.WebSite.strip()
                    if membre.HomePhone and membre.HomePhone.strip():
                        value["phone"] = membre.HomePhone.strip()
                    if membre.WorkPhone and membre.WorkPhone.strip():
                        value["mobile"] = membre.WorkPhone.strip()

                    # TODO add "create_date": membre.Date_MAJ_Membre, into mail message

                    # if membre.Memo:
                    #     value["comment"] = membre.Memo.strip()
                    #
                    # if city_name:
                    #     value["city"] = city_name.Ville
                    #
                    # self._set_phone(membre, value)

                    obj_partner = env["res.partner"].create(value)
                    dct_partner[membre.UserID] = obj_partner
                    # try:
                    #     obj_partner = env["res.partner"].create(value)
                    # except Exception as e:
                    #     self.lst_error.append(e)
                    #     _logger.error(e)
                    #     continue
                    if membre.UserID == DEFAULT_SELL_USER_ID:

                        value = {
                            "name": obj_partner.name,
                            "active": True,
                            "login": email,
                            # "password": membre.MotDePasseRaw,
                            "email": email,
                            # "groups_id": groups_id,
                            # "company_id": company_id.id,
                            # "company_ids": [(4, company_id.id)],
                            "partner_id": obj_partner.id,
                        }

                        obj_user = (
                            env["res.users"]
                            # .with_context(
                            #     {"no_reset_password": no_reset_password}
                            # )
                            .create(value)
                        )

                        self.dct_res_user[membre.UserID] = obj_user
                #
                #     _logger.info(
                #         f"{pos_id} - res.users - tbl_membre -"
                #         f" '{type_member}' - ADDED '{name}' login"
                #         f" '{login}' email '{email}' id {membre.NoMembre}"
                #     )

                # related: nom, active, adresse, codepostal, logo, telephone1, courriel
                # value_membre = {
                #     "companie": companie_companie_id.id,
                #     "point_service": companie_point_service_id.id,
                #     # "type_communication": membre.NoTypeCommunication,
                #     # "occupation": membre.NoOccupation,
                #     # "origine": membre.NoOrigine,
                #     # "situation_maison": membre.NoSituationMaison,
                #     # "provenance": membre.NoProvenance,
                #     # "revenu_familial": membre.NoRevenuFamilial,
                #     # "arrondissement": membre.NoArrondissement,
                #     # "ville": membre.NoVille,
                #     # "region": membre.NoRegion,
                #     "membre_ca": membre.MembreCA,
                #     "part_social_paye": membre.PartSocialPaye,
                #     "date_adhesion": membre.DateAdhesion,
                #     # "adresse": membre.Adresse,
                #     "telephone_1": membre.Telephone1,
                #     "telephone_poste_1": membre.PosteTel1,
                #     "telephone_2": membre.Telephone2,
                #     "telephone_poste_2": membre.PosteTel2,
                #     "telephone_3": membre.Telephone3,
                #     "telephone_poste_3": membre.PosteTel3,
                #     "achat_regrouper": membre.AchatRegrouper,
                #     "pret_actif": membre.PretActif,
                #     "bottin_tel": membre.BottinTel,
                #     "bottin_courriel": membre.BottinCourriel,
                #     "membre_conjoint": membre.MembreConjoint,
                #     "membre_conjoint_id": membre.MembreConjoint,
                #     # "memo": membre.Memo,
                #     # "sexe": membre.Sexe,
                #     "annee_naissance": membre.AnneeNaissance,
                #     "nom_utilisateur": membre.NomUtilisateur,
                #     "profil_approuver": membre.ProfilApprouver,
                #     "membre_principal": membre.MembrePrinc,
                #     "recevoir_courriel_groupe": membre.RecevoirCourrielGRP,
                #     "pas_communication": membre.PasCommunication,
                #     "description_membre": membre.DescriptionAccordeur,
                #     "region": 1,
                #     "ville": 1,
                #     # "create_date": membre.Date_MAJ_Membre,
                # }
                # if membre.NoTypeTel1 and membre.NoTypeTel1 > 1:
                #     value_membre["telephone_type_1"] = (
                #         membre.NoTypeTel1 - 1
                #     )
                # if membre.NoTypeTel2 and membre.NoTypeTel2 > 1:
                #     value_membre["telephone_type_2"] = (
                #         membre.NoTypeTel2 - 1
                #     )
                # if membre.NoTypeTel3 and membre.NoTypeTel3 > 1:
                #     value_membre["telephone_type_3"] = (
                #         membre.NoTypeTel3 - 1
                #     )
                #
                # if associate_point_service:
                #     value_membre["partner_id"] = associate_point_service.id
                # else:
                #     value_membre["partner_id"] = obj_partner.id
                #
                # if companie_companie_transfer_de_id:
                #     value_membre[
                #         "transfert_companie"
                #     ] = companie_companie_transfer_de_id.id
                #
                # obj_companie_membre = env["companie.membre"].create(
                #     value_membre
                # )
                # point_service_info = (
                #     " - POINT_SERVICE" if membre.EstUnPointService else ""
                # )
                # _logger.info(
                #     f"{pos_id} - companie.membre - tbl_membre -"
                #     f" '{type_member}'{point_service_info} - ADDED"
                #     f" '{name}' login '{login}' email '{email}' id"
                #     f" {obj_companie_membre.id}"
                # )
                # dct_companie_membre[
                #     membre.NoMembre
                # ] = obj_companie_membre

                # Add migration message
                # comment_message = (
                #     "<b>Note de migration</b><br/>Dernière mise à"
                #     f" jour : {membre.Date_MAJ_Membre}"
                # )

                # comment_value = {
                #     "subject": (
                #         "Note de migration - Plateforme Espace Membre"
                #     ),
                #     "body": f"<p>{comment_message}</p>",
                #     "parent_id": False,
                #     "message_type": "comment",
                #     "author_id": SUPERUSER_ID,
                #     "model": "companie.membre",
                #     "res_id": obj_companie_membre.id,
                # }
                # env["mail.message"].create(comment_value)
                #
                # # Add memo message
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

            self.dct_membre = dct_membre
            self.dct_partner = dct_partner
            self.dct_companie_membre = dct_companie_membre
            _logger.info(
                f"Stat: {nb_admin} admin and {nb_membre_int} membre"
                f" interne and {nb_membre_ext} membre externe."
            )

    def _get_permission_no_membre(self, no_membre):
        tpl_access = [
            a for a in self.dct_tbl.tbl_droits_admin if a.NoMembre == no_membre
        ]
        if tpl_access:
            return tpl_access[0]

    def _get_type_compte_no_membre(self, no_membre):
        tpl_access = [
            a for a in self.dct_tbl.tbl_type_compte if a.NoMembre == no_membre
        ]
        if tpl_access:
            return tpl_access[0]

    def migrate_product_category(self):
        """
        :return:
        """
        _logger.info("Migrate product_category")
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_product_category:
            return
        dct_result = {}

        lst_tbl_store_categorie = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreCategories"
        )

        for pos_id, categorie in enumerate(lst_tbl_store_categorie):
            # TODO AffiliateLinks
            name = categorie.CategoryNameFR
            value_categorie = {
                "name": name,
            }
            categorie_id = env["product.category"].create(value_categorie)
            dct_result[categorie.CategoryID] = categorie_id
            _logger.info(
                f"{pos_id} - product.category - tbStoreCategories - ADDED"
                f" '{name}' id {categorie.CategoryID}"
            )

        self.dct_product_category = dct_result

    def migrate_slide_channel(self):
        """
        :return:
        """
        _logger.info("Migrate slide_channel")
        # TODO create with administrator user and not bot
        env = api.Environment(self.cr, SUPERUSER_ID, {})
        if self.dct_slide_channel:
            return
        dct_slide_channel = {}
        i = 0
        # Set a default seller
        default_seller_id = self.dct_partner[DEFAULT_SELL_USER_ID]
        default_seller_id.seller = True
        default_seller_id.url_handler = default_seller_id.name.replace(
            " ", "_"
        )
        default_user_seller_id = self.dct_res_user[DEFAULT_SELL_USER_ID]
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
        # TODO configure tax quebec
        # Configure to allow no suspens
        journal_id.inbound_payment_method_line_ids[
            0
        ].payment_account_id = journal_id.default_account_id.id
        journal_id.outbound_payment_method_line_ids[
            0
        ].payment_account_id = journal_id.default_account_id.id
        sale_tax_id = env["account.tax"].search(
            [
                (
                    "description",
                    "=",
                    env.ref(f"l10n_ca.gstqst_sale_en").description,
                ),
                ("type_tax_use", "=", "sale"),
            ],
            limit=1,
        )
        purchase_tax_id = env["account.tax"].search(
            [
                (
                    "description",
                    "=",
                    env.ref(f"l10n_ca.gstqst_purc_en").description,
                ),
                ("type_tax_use", "=", "purchase"),
            ],
            limit=1,
        )

        env.company.write(
            {
                "account_sale_tax_id": sale_tax_id.id,
                "account_purchase_tax_id": purchase_tax_id.id,
            }
        )
        # TODO
        #  lst_tbl_content pour le contenu des pages web
        #  lst_tbl_store_item pour article/produit

        i = 0
        lst_tbl_slide_channel = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbTrainingCourses"
        )
        lst_tbl_content = self.dct_tbl.get(f"{self.db_name}.dbo.tbContents")
        lst_tbl_coupon_allowed_item = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbCouponAllowedItems"
        )
        lst_tbl_store_item_animator = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreItemAnimators"
        )
        lst_tbl_store_item_content_package_mapping = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreItemContentPackageMappings"
        )
        lst_tbl_store_item_content_package = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreItemContentPackages"
        )
        lst_tbl_store_item_content_type = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreItemContentTypes"
        )
        lst_tbl_store_item_contents = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreItemContents"
        )
        lst_tbl_store_item_picture = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreItemPictures"
        )
        lst_tbl_store_item = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreItems"
        )
        lst_tbl_store_item_variant = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreItemVariants"
        )
        lst_tbl_store_shopping_cart_item_coupons = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreShoppingCartItemCoupons"
        )
        lst_tbl_store_shopping_cart_item = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreShoppingCartItems"
        )
        lst_tbl_store_shopping_cart = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbStoreShoppingCarts"
        )
        lst_tbl_knowledge_answer_results = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbKnowledgeAnswerResults"
        )
        lst_tbl_knowledge_test_results = self.dct_tbl.get(
            f"{self.db_name}.dbo.tbKnowledgeTestResults"
        )

        for slide_channel in lst_tbl_slide_channel:
            i += 1
            pos_id = f"{i}/{len(lst_tbl_slide_channel)}"

            if DEBUG_LIMIT and i > LIMIT:
                break

            name = slide_channel.CourseName

            # city_name = self._get_ville(slide_channel.NoVille)

            # Slide Channel
            # TODO Duration -> create a statistics, check _compute_slides_statistics
            # Ignore CourseID
            # TODO ReleaseDate
            # TODO TestID
            value = {
                "name": name,
                # "description": slide_channel.Description.strip(),
                "is_published": True,
                "visibility": "public",
                "enroll": "payment",
                "create_date": slide_channel.CreatedDate,
                "seller_id": default_seller_id.id,
                "user_id": default_user_seller_id.id,
            }

            obj_slide_channel_id = env["slide.channel"].create(value)

            dct_slide_channel[slide_channel.CourseID] = obj_slide_channel_id
            _logger.info(
                f"{pos_id} - slide.channel - tbl_slide_channel - ADDED"
                f" '{name}' id {slide_channel.CourseID}"
            )
            # Support TestId
            test_id_tbl = slide_channel.TestID

            # Survey.survey init
            lbl_knowledge_test = f"{self.db_name}.dbo.tbKnowledgeTests"
            lst_tbl_knowledge_test = self.dct_tbl.get(lbl_knowledge_test)
            lst_knowledge_test_tbl = [
                a for a in lst_tbl_knowledge_test if a.TestID == test_id_tbl
            ]
            if not lst_knowledge_test_tbl:
                _logger.warning(
                    f"About tbKnowledgeTests, missing TestID {test_id_tbl}"
                )
                continue
            knowledge_test_tbl = lst_knowledge_test_tbl[0]

            obj_slide_channel_id.description = (
                knowledge_test_tbl.CertificateBodyFR
            )

            # Survey.question init
            lbl_knowledge_question = f"{self.db_name}.dbo.tbKnowledgeQuestions"
            lst_tbl_knowledge_question = self.dct_tbl.get(
                lbl_knowledge_question
            )
            lst_knowledge_question_tbl = [
                a
                for a in lst_tbl_knowledge_question
                if a.TestID == test_id_tbl
            ]
            if not lst_knowledge_question_tbl:
                _logger.warning(
                    f"About tbKnowledgeQuestions, missing TestID {test_id_tbl}"
                )
                continue

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
            self.dct_survey[knowledge_test_tbl.TestID] = obj_survey

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
                self.dct_question[
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
                    _logger.warning(
                        "About tbKnowledgeAnswerChoices, missing"
                        f" QuestionID {tbl_knowledge_question_id}"
                    )
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
                    self.dct_survey_question_answer[
                        knowledge_question_answer_tbl.AnswerID
                    ] = question_answer_id

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
            self.dct_slide_survey_id[obj_survey.id] = obj_slide

        # Import result survey
        for tbl_knowledge_test_results in lst_tbl_knowledge_test_results:
            partner_id = self.dct_partner.get(
                tbl_knowledge_test_results.UserID
            )
            if not partner_id:
                _logger.error(
                    "Cannot find partner_id for UserID"
                    f" '{tbl_knowledge_test_results.UserID}'"
                )
                continue

            obj_survey = self.dct_survey.get(tbl_knowledge_test_results.TestID)
            if not obj_survey:
                _logger.error(
                    "Cannot find survey for TestID"
                    f" '{tbl_knowledge_test_results.TestID}'"
                )
                continue
            # DONE Ignore Grade, will be recalcul, validate the value is good by a warning
            # DONE validate IsSuccessful
            # TODO start date and end date is the same
            # DONE last_displayed_page_id select last question id
            obj_slide = self.dct_slide_survey_id[obj_survey.id]

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

            # Get associate result line
            lst_associate_answer_result = [
                a
                for a in lst_tbl_knowledge_answer_results
                if a.TestResultID == tbl_knowledge_test_results.TestResultID
            ]
            survey_question_answer = None
            obj_survey_user_input_line = None
            for associate_answer_result in lst_associate_answer_result:
                survey_question_answer = self.dct_survey_question_answer[
                    associate_answer_result.AnswerID
                ]
                # TODO answer_score
                # TODO answer_is_correct
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
        for store_item in lst_tbl_store_item:
            # ? ItemOrder
            # ? ItemShippingFee
            # DateCreated
            # ItemSellPrice
            # ItemBuyCost
            # ItemDescriptionFR
            # ItemDescriptionExtentedFR
            if store_item.CategoryID in (1, 2):
                value_event = {
                    "name": store_item.ItemNameFR,
                    "user_id": default_user_seller_id.id,
                    "organizer_id": default_seller_id.id,
                    "create_date": store_item.DateCreated,
                    "date_begin": store_item.DateCreated,
                    "date_end": store_item.DateCreated,
                    "date_tz": "America/Montreal",
                    "is_published": store_item.IsOnHomePage,
                    "active": store_item.IsActive,
                }
                event_id = env["event.event"].create(value_event)
                self.dct_event[store_item.ItemID] = event_id
                # TODO missing ItemBuyCost
                price = store_item.ItemSellPrice / 1.14975
                value_event_ticket = {
                    "name": store_item.ItemNameFR,
                    "event_id": event_id.id,
                    "product_id": env.ref(
                        "event_sale.product_product_event"
                    ).id,
                    "price": price,
                    "create_date": store_item.DateCreated,
                }
                event_ticket_id = env["event.event.ticket"].create(
                    value_event_ticket
                )
                self.dct_event_ticket[store_item.ItemID] = event_ticket_id
            else:
                categorie = self.dct_product_category.get(
                    store_item.CategoryID
                )
                value_product = {
                    "name": store_item.ItemNameFR,
                    "list_price": store_item.ItemSellPrice / 1.14975,
                    "standard_price": store_item.ItemBuyCost,
                    "create_date": store_item.DateCreated,
                    "categ_id": categorie.id,
                    "is_published": store_item.IsOnHomePage,
                    "active": store_item.IsActive,
                }
                product_template_id = env["product.template"].create(
                    value_product
                )
                self.dct_product_template[
                    store_item.ItemID
                ] = product_template_id

        for store_shopping_cart in lst_tbl_store_shopping_cart:
            if (
                not store_shopping_cart.IsCompleted
                and store_shopping_cart.ProviderStatusText != "completed"
            ):
                continue
            i += 1
            if DEBUG_LIMIT and i > LIMIT:
                continue
            order_partner_id = self.dct_partner.get(store_shopping_cart.UserID)
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
                "date_order": store_shopping_cart.DateCreated,
                "create_date": store_shopping_cart.DateCreated,
                "partner_id": order_partner_id.id,
                # "is_published": store_item.IsActive,
                "state": "done",
            }
            sale_order_id = env["sale.order"].create(value_sale_order)
            # move.action_post()
            self.dct_sale_order[store_shopping_cart.CartID] = sale_order_id
            lst_items = [
                a
                for a in lst_tbl_store_shopping_cart_item
                if a.CartID == store_shopping_cart.CartID
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
                    "create_date": store_shopping_cart.DateCreated,
                    "order_partner_id": order_partner_id.id,
                    "order_id": sale_order_id.id,
                    "price_unit": store_shopping_cart.TotalAmount / 1.14975,
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
                    f" {store_shopping_cart.CartID}"
                )
            else:
                for item in lst_items:
                    product_shopping_id = self.dct_product_template.get(
                        item.ItemID
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
                        "create_date": store_shopping_cart.DateCreated,
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
            try:
                i += 1
                if DEBUG_LIMIT and i < LIMIT or not DEBUG_LIMIT:
                    # Validate sale order
                    # sale_order_id.action_confirm()

                    # Create Invoice
                    invoice_vals = {
                        "move_type": "out_invoice",  # for customer invoice
                        "partner_id": sale_order_id.partner_id.id,
                        "journal_id": journal_sale_id.id,
                        "date": store_shopping_cart.DateCreated,
                        "invoice_date": store_shopping_cart.DateCreated,
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
                            "date": store_shopping_cart.DateCreated,
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
            except Exception as e:
                _logger.error(e)

        self.dct_slide_channel = dct_slide_channel

    def _get_ville(self, no_ville: int):
        for ville in self.dct_tbl.tbl_ville:
            if ville.NoVille == no_ville:
                return ville

    def _get_membre(self, no_membre: int):
        for membre in self.dct_tbl.tbl_membre:
            if membre.NoMembre == no_membre:
                return membre

    def _get_membre_point_service(self, no_point_service: int):
        for membre in self.dct_tbl.tbl_membre:
            if (
                membre.NoPointService == no_point_service
                and membre.EstUnPointService
            ):
                return membre

    def _set_phone(self, membre, value):
        # Manage phone
        # result 22, 25, 28 is type
        # Type: 1 choose (empty)
        # Type: 2 domicile Phone
        # Type: 3 Travail À SUPPORTÉ
        # Type: 4 Cellulaire MOBILE
        # Type: 5 Téléavertisseur (pagette) NON SUPPORTÉ

        # Pagette
        if (
            membre.NoTypeTel1 == 5
            or membre.NoTypeTel2 == 5
            or membre.NoTypeTel3 == 5
        ):
            msg = (
                "Le pagette n'est pas supporté pour le membre"
                f" {membre.NoMembre}."
            )
            _logger.warning(msg)
            self.lst_warning.append(msg)

        # Travail
        if (
            membre.NoTypeTel1 == 3
            or membre.NoTypeTel2 == 3
            or membre.NoTypeTel3 == 3
        ):
            msg = (
                "Le téléphone travail n'est pas supporté pour le membre"
                f" {membre.NoMembre}."
            )
            _logger.warning(msg)
            self.lst_warning.append(msg)

        # MOBILE
        has_mobile = False
        if (
            membre.NoTypeTel1 == 4
            and membre.Telephone1
            and membre.Telephone1.strip()
        ):
            has_mobile = True
            value["mobile"] = membre.Telephone1.strip()
            if membre.PosteTel1 and membre.PosteTel1.strip():
                msg = (
                    "Le numéro de poste du mobile n'est pas supporté pour le"
                    f" membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
        if (
            membre.NoTypeTel2 == 4
            and membre.Telephone2
            and membre.Telephone2.strip()
        ):
            if has_mobile:
                msg = (
                    f"Duplicat du cellulaire pour le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            else:
                has_mobile = True
                value["mobile"] = membre.Telephone2.strip()
                if membre.PosteTel2 and membre.PosteTel2.strip():
                    msg = (
                        "Le numéro de poste du mobile n'est pas supporté pour"
                        f" le membre {membre.NoMembre}."
                    )
                    _logger.warning(msg)
                    self.lst_warning.append(msg)
        if (
            membre.NoTypeTel3 == 4
            and membre.Telephone3
            and membre.Telephone3.strip()
        ):
            if has_mobile:
                msg = (
                    f"Duplicat du cellulaire pour le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            else:
                has_mobile = True
                value["mobile"] = membre.Telephone3.strip()
                if membre.PosteTel3 and membre.PosteTel3.strip():
                    msg = (
                        "Le numéro de poste du mobile n'est pas supporté pour"
                        f" le membre {membre.NoMembre}."
                    )
                    _logger.warning(msg)
                    self.lst_warning.append(msg)

        has_domicile = False
        if (
            membre.NoTypeTel1 == 2
            and membre.Telephone1
            and membre.Telephone1.strip()
        ):
            has_domicile = True
            value["phone"] = membre.Telephone1.strip()
            if (
                membre.PosteTel1
                and membre.PosteTel1
                and membre.PosteTel1.strip()
            ):
                msg = (
                    "Le numéro de poste du domicile n'est pas supporté pour"
                    f" le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
        if (
            membre.NoTypeTel2 == 2
            and membre.Telephone2
            and membre.Telephone2.strip()
        ):
            if has_domicile:
                msg = (
                    f"Duplicat du cellulaire pour le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            else:
                has_domicile = True
                value["phone"] = membre.Telephone2.strip()
                if membre.PosteTel2 and membre.PosteTel2.strip():
                    msg = (
                        "Le numéro de poste du domicile n'est pas supporté"
                        f" pour le membre {membre.NoMembre}."
                    )
                    _logger.warning(msg)
                    self.lst_warning.append(msg)
        if (
            membre.NoTypeTel3 == 2
            and membre.Telephone3
            and membre.Telephone3.strip()
        ):
            if has_domicile:
                msg = (
                    f"Duplicat du cellulaire pour le membre {membre.NoMembre}."
                )
                _logger.warning(msg)
                self.lst_warning.append(msg)
            else:
                has_domicile = True
                value["phone"] = membre.Telephone3.strip()
                if membre.PosteTel3 and membre.PosteTel3.strip():
                    msg = (
                        "Le numéro de poste du domicile n'est pas supporté"
                        f" pour le membre {membre.NoMembre}."
                    )
                    _logger.warning(msg)
                    self.lst_warning.append(msg)

    def _check_duplicate(self, tbl_membre, key, verbose=True):
        # Ignore duplicate since enable multi-company with different contact, not sharing
        # Debug duplicate data, need unique name
        dct_debug = collections.defaultdict(list)
        for result in tbl_membre:
            key_info = result.__dict__.get(key)
            if key_info is None:
                key_info = ""
            else:
                key_info = key_info.lower().strip()

            dct_debug[key_info].append(result)
        lst_to_remove = []
        for key_info, value in dct_debug.items():
            if len(value) > 1:
                if verbose:
                    _logger.warning(
                        f"Duplicate name ({len(value)})"
                        f" {key_info.lower().strip()}: {value}\n"
                    )
            else:
                lst_to_remove.append(key_info.lower().strip())
        for key_info in lst_to_remove:
            del dct_debug[key_info]
        return dct_debug
