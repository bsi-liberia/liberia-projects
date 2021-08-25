from projectdashboard import models
from projectdashboard.extensions import db
from projectdashboard.query import activity as qactivity

import sqlalchemy as sa
from sqlalchemy.sql import func


def aggregate(dimension, req_filters=[], req_finances_joins=[], req_forwardspends_joins=[]):
    query_finances = [func.sum(models.ActivityFinances.transaction_value).label("total_value"),
                      models.ActivityFinances.transaction_type,
                      models.Activity.domestic_external,
                      models.FiscalYear.name.label("fiscal_year")]

    query_forwardspends = [func.sum(models.ActivityForwardSpend.value).label("total_value"),
                           sa.sql.expression.literal(
                               "FS").label("transaction_type"),
                           models.Activity.domestic_external,
                           models.FiscalYear.name.label("fiscal_year")]

    query_join = [models.Activity, models.FiscalPeriod, models.FiscalYear]

    query_finances_filters = [
        models.Activity.domestic_external == 'external', ] + req_filters

    if dimension in ['mtef-sector', 'papd-pillar', 'sdg-goals']:
        query_finances += [models.CodelistCode.code, models.CodelistCode.name]
        query_forwardspends += [models.CodelistCode.code,
                                models.CodelistCode.name]

        # MTEF Sectors are set on ActivityFinances;
        # other classifications are set on Activity
        if dimension == 'mtef-sector':
            query_finances_join = query_join + [models.ActivityFinancesCodelistCode,
                                                models.CodelistCode] + req_finances_joins
        else:
            query_finances_join = query_join + [models.ActivityCodelistCode,
                                                models.CodelistCode] + req_finances_joins

        query_forwardspends_join = query_join + [models.ActivityCodelistCode,
                                                 models.CodelistCode] + req_forwardspends_joins
        query_finances_filters += [models.CodelistCode.codelist_code == dimension]
        query_forwardspends_filters = query_finances_filters
        group_by = [models.CodelistCode.name,
                    models.CodelistCode.code, models.FiscalYear.name]

    elif dimension in ['reporting-org']:
        query_finances += [models.Activity.reporting_org_id.label("code"),
                           models.Organisation.name]
        query_forwardspends += [models.Activity.reporting_org_id.label("code"),
                                models.Organisation.name]
        query_finances_join = [(models.Activity, models.ActivityFinances.activity_id == models.Activity.id), (models.Organisation,
                                                                                                              models.Activity.reporting_org_id == models.Organisation.id), models.FiscalPeriod, models.FiscalYear] + req_finances_joins
        query_forwardspends_join = [(models.Activity, models.ActivityForwardSpend.activity_id == models.Activity.id), (
            models.Organisation, models.Activity.reporting_org_id == models.Organisation.id)] + req_forwardspends_joins
        query_forwardspends_filters = query_finances_filters
        group_by = [models.Activity.reporting_org_id,
                    models.Organisation.name, models.FiscalYear]

    query_finances_groupby = group_by + [models.ActivityFinances.transaction_type,
                                         models.Activity.domestic_external]

    query_forwardspends_groupby = group_by + ["transaction_type",
                                              models.Activity.domestic_external]

    query = db.session.query(
        *query_finances
    )
    for _join in query_finances_join:
        query = query.outerjoin(_join)
    query = query.filter(
        *query_finances_filters
    ).group_by(
        *query_finances_groupby
    )
    query = qactivity.filter_activities_for_permissions(query)
    sector_totals = query.all()

    fy_query = db.session.query(
        *query_forwardspends
    )
    for _join in query_forwardspends_join:
        fy_query = fy_query.outerjoin(_join)
    fy_query = fy_query.filter(
        *query_forwardspends_filters
    ).group_by(
        *query_forwardspends_groupby
    )
    fy_query = qactivity.filter_activities_for_permissions(fy_query)
    fy_sector_totals = fy_query.all()

    return sector_totals+fy_sector_totals
