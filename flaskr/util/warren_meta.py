import statistics
import traceback
import math

from ..models import StatementTimeFrame
from .. import models


def convert_keys_to_string(d):
    if isinstance(d, dict):
        return {str(k): convert_keys_to_string(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_keys_to_string(i) for i in d]
    else:
        return d


def gross_profit_meta(statement, stock_meta: models.StockMeta, stock_id):
    try:
        # gross profit check.
        # get yearly/quaterly data from stock_meta object based on current statement's time frame.
        existing_meta_for_timeframe = getattr(
            stock_meta, statement["_id"]["time_frame"], {}
        )

        if "gross_profit_margin" in existing_meta_for_timeframe:
            gross_profit_stock_meta = existing_meta_for_timeframe["gross_profit_margin"]
        else:
            gross_profit_stock_meta = {}

        # Add new quarterly/yearly data to periods.
        existing_periods: dict = gross_profit_stock_meta.get("periods", {})
        for i, document in enumerate(statement["documents"]):
            if stock_id is None and "stock_id" in document:
                stock_meta.stock_id = stock_id = document["stock_id"]
            if str(document["statement_date"]) in existing_periods:
                if i == 0:
                    return stock_meta
                break
            doc_data = document.get("data", {})
            if (
                "GrossProfit" not in doc_data
                or "TotalRevenue" not in doc_data
                or math.isnan(doc_data["GrossProfit"])
                or math.isnan(doc_data["TotalRevenue"])
                or doc_data["TotalRevenue"] == 0
            ):
                gross_profit_margin = 0
            else:
                gross_profit_margin = doc_data["GrossProfit"] / doc_data["TotalRevenue"]
            existing_periods[str(document["statement_date"])] = gross_profit_margin

        gross_profit_stock_meta["periods"] = existing_periods

        # Create dates and values array
        dates = []
        values = []
        sorted_existing_periods_dates = sorted(existing_periods.keys())
        for date in sorted_existing_periods_dates:
            dates.append(date)
            values.append(existing_periods[date])
        gross_profit_stock_meta["dates"] = dates
        gross_profit_stock_meta["values"] = values

        # compute mean, variance and stdev
        gross_profit_stock_meta["mean"] = statistics.mean(values)
        gross_profit_stock_meta["variance"] = statistics.variance(values)
        gross_profit_stock_meta["stdev"] = statistics.stdev(values)

        # assign back variables
        existing_meta_for_timeframe["gross_profit_margin"] = gross_profit_stock_meta

    except Exception as e:
        print("Error in gross_profit_meta")
        traceback.print_exc()
    return stock_meta


def sga_meta(statement, stock_meta: models.StockMeta):
    try:
        # gross profit check.
        # get yearly/quaterly data from stock_meta object based on current statement's time frame.
        existing_meta_for_timeframe = getattr(
            stock_meta, statement["_id"]["time_frame"], {}
        )

        if "sga_to_profit" in existing_meta_for_timeframe:
            existing_stock_meta = existing_meta_for_timeframe["sga_to_profit"]
        else:
            existing_stock_meta = {}

        # Add new quarterly/yearly data to periods.
        existing_periods: dict = existing_stock_meta.get("periods", {})
        for i, document in enumerate(statement["documents"]):
            if str(document["statement_date"]) in existing_periods:
                if i == 0:
                    return stock_meta
                break
            doc_data = document.get("data", {})
            if (
                "SellingGeneralAndAdministration" not in doc_data
                or math.isnan(doc_data["SellingGeneralAndAdministration"])
                and "GrossProfit" in doc_data
                and math.isnan(doc_data["GrossProfit"])
                and doc_data["GrossProfit"] > 0
            ):
                sga_to_profit = 0
            elif (
                "GrossProfit" not in doc_data
                or math.isnan(doc_data["GrossProfit"])
                or doc_data["GrossProfit"] == 0
            ):
                sga_to_profit = 1
            else:
                sga_to_profit = (
                    doc_data["SellingGeneralAndAdministration"]
                    / doc_data["GrossProfit"]
                )
            existing_periods[str(document["statement_date"])] = sga_to_profit

        existing_stock_meta["periods"] = existing_periods

        # Create dates and values array
        dates = []
        values = []
        sorted_existing_periods_dates = sorted(existing_periods.keys())
        for date in sorted_existing_periods_dates:
            dates.append(date)
            values.append(existing_periods[date])
        existing_stock_meta["dates"] = dates
        existing_stock_meta["values"] = values

        # compute mean, variance and stdev
        existing_stock_meta["mean"] = statistics.mean(values)
        existing_stock_meta["variance"] = statistics.variance(values)
        existing_stock_meta["stdev"] = statistics.stdev(values)

        # assign back variables
        existing_meta_for_timeframe["sga_to_profit"] = existing_stock_meta
    except Exception as e:
        print("Error in sga_meta")
        traceback.print_exc()


def rnd_meta(statement, stock_meta: models.StockMeta):
    try:
        # get yearly/quaterly data from stock_meta object based on current statement's time frame.
        existing_meta_for_timeframe = getattr(
            stock_meta, statement["_id"]["time_frame"], {}
        )

        if "rnd_to_profit" in existing_meta_for_timeframe:
            existing_stock_meta = existing_meta_for_timeframe["rnd_to_profit"]
        else:
            existing_stock_meta = {}

        # Add new quarterly/yearly data to periods.
        existing_periods: dict = existing_stock_meta.get("periods", {})
        for i, document in enumerate(statement["documents"]):
            if str(document["statement_date"]) in existing_periods:
                if i == 0:
                    return stock_meta
                break
            doc_data = document.get("data", {})
            if (
                "ResearchAndDevelopment" not in doc_data
                or "GrossProfit" not in doc_data
                or math.isnan(doc_data["ResearchAndDevelopment"])
                or math.isnan(doc_data["GrossProfit"])
                or doc_data["GrossProfit"] == 0
            ):
                value = 0
            else:
                value = doc_data["ResearchAndDevelopment"] / doc_data["GrossProfit"]
            existing_periods[str(document["statement_date"])] = value

        existing_stock_meta["periods"] = existing_periods

        # Create dates and values array
        dates = []
        values = []
        sorted_existing_periods_dates = sorted(existing_periods.keys())
        for date in sorted_existing_periods_dates:
            dates.append(date)
            values.append(existing_periods[date])
        existing_stock_meta["dates"] = dates
        existing_stock_meta["values"] = values

        # compute mean, variance and stdev
        existing_stock_meta["mean"] = statistics.mean(values)
        existing_stock_meta["variance"] = statistics.variance(values)
        existing_stock_meta["stdev"] = statistics.stdev(values)

        # assign back variables
        existing_meta_for_timeframe["rnd_to_profit"] = existing_stock_meta
    except Exception as e:
        print("Error in sga_meta")
        traceback.print_exc()


def depreciation_meta(statement, stock_meta: models.StockMeta):
    try:
        # get yearly/quaterly data from stock_meta object based on current statement's time frame.
        existing_meta_for_timeframe = getattr(
            stock_meta, statement["_id"]["time_frame"], {}
        )

        if "rnd_to_profit" in existing_meta_for_timeframe:
            existing_stock_meta = existing_meta_for_timeframe["rnd_to_profit"]
        else:
            existing_stock_meta = {}

        # Add new quarterly/yearly data to periods.
        existing_periods: dict = existing_stock_meta.get("periods", {})
        for i, document in enumerate(statement["documents"]):
            if str(document["statement_date"]) in existing_periods:
                if i == 0:
                    return stock_meta
                break
            doc_data = document.get("data", {})
            if (
                "ResearchAndDevelopment" not in doc_data
                or "GrossProfit" not in doc_data
                or math.isnan(doc_data["ResearchAndDevelopment"])
                or math.isnan(doc_data["GrossProfit"])
                or doc_data["GrossProfit"] == 0
            ):
                value = 0
            else:
                value = doc_data["ResearchAndDevelopment"] / doc_data["GrossProfit"]
            existing_periods[str(document["statement_date"])] = value

        existing_stock_meta["periods"] = existing_periods

        # Create dates and values array
        dates = []
        values = []
        sorted_existing_periods_dates = sorted(existing_periods.keys())
        for date in sorted_existing_periods_dates:
            dates.append(date)
            values.append(existing_periods[date])
        existing_stock_meta["dates"] = dates
        existing_stock_meta["values"] = values

        # compute mean, variance and stdev
        existing_stock_meta["mean"] = statistics.mean(values)
        existing_stock_meta["variance"] = statistics.variance(values)
        existing_stock_meta["stdev"] = statistics.stdev(values)

        # assign back variables
        existing_meta_for_timeframe["rnd_to_profit"] = existing_stock_meta
    except Exception as e:
        print("Error in sga_meta")
        traceback.print_exc()


def common_meta(statement, stock_meta: models.StockMeta, stock_id):
    try:
        # get yearly/quaterly data from stock_meta object based on current statement's time frame.
        existing_meta_for_timeframe = getattr(
            stock_meta, statement["_id"]["time_frame"], {}
        )
        existing_metas = {}
        if "gross_profit_margin" in existing_meta_for_timeframe:
            existing_metas["gross_profit_margin"] = existing_meta_for_timeframe[
                "gross_profit_margin"
            ]
        else:
            existing_metas["gross_profit_margin"] = {}

        if "sga_to_profit" in existing_meta_for_timeframe:
            existing_metas["sga_to_profit"] = existing_meta_for_timeframe[
                "sga_to_profit"
            ]
        else:
            existing_metas["sga_to_profit"] = {}

        if "rnd_to_profit" in existing_meta_for_timeframe:
            existing_metas["rnd_to_profit"] = existing_meta_for_timeframe[
                "rnd_to_profit"
            ]
        else:
            existing_metas["rnd_to_profit"] = {}

        if "depreciation_to_profit" in existing_meta_for_timeframe:
            existing_metas["depreciation_to_profit"] = existing_meta_for_timeframe[
                "depreciation_to_profit"
            ]
        else:
            existing_metas["depreciation_to_profit"] = {}

        if "intrest_payout_to_operating_income" in existing_meta_for_timeframe:
            existing_metas["intrest_payout_to_operating_income"] = (
                existing_meta_for_timeframe["intrest_payout_to_operating_income"]
            )
        else:
            existing_metas["intrest_payout_to_operating_income"] = {}

        if "net_earnings" in existing_meta_for_timeframe:
            existing_metas["net_earnings"] = existing_meta_for_timeframe["net_earnings"]
        else:
            existing_metas["net_earnings"] = {}

        if "earnings_to_revenue" in existing_meta_for_timeframe:
            existing_metas["earnings_to_revenue"] = existing_meta_for_timeframe[
                "earnings_to_revenue"
            ]
        else:
            existing_metas["earnings_to_revenue"] = {}

        if "eps" in existing_meta_for_timeframe:
            existing_metas["eps"] = existing_meta_for_timeframe["eps"]
        else:
            existing_metas["eps"] = {}

        # Add new quarterly/yearly data to periods.
        existing_periods_dict: dict = {
            k: existing_meta.get("periods", {})
            for k, existing_meta in existing_metas.items()
        }
        stop_processing = {k: False for k in existing_metas.keys()}
        for i, document in enumerate(statement["documents"]):
            if stock_id is None and "stock_id" in document:
                stock_meta.stock_id = stock_id = document["stock_id"]
            for k, existing_periods in existing_periods_dict.items():
                if (
                    stop_processing[k] == False
                    and str(document["statement_date"]) in existing_periods
                ):
                    stop_processing[k] = True

            if list(stop_processing.values()).all(True):
                if i == 0:
                    return
                break

            doc_data = document.get("data", {})
            # gross profit meta
            if stop_processing["gross_profit_margin"] == False:
                if (
                    "GrossProfit" not in doc_data
                    or "TotalRevenue" not in doc_data
                    or math.isnan(doc_data["GrossProfit"])
                    or math.isnan(doc_data["TotalRevenue"])
                    or doc_data["TotalRevenue"] == 0
                ):
                    gross_profit_margin = 0
                else:
                    gross_profit_margin = (
                        doc_data["GrossProfit"] / doc_data["TotalRevenue"]
                    )
                existing_periods_dict["gross_profit_margin"][
                    str(document["statement_date"])
                ] = gross_profit_margin

            compute_ratio_meta(
                doc_data=doc_data,
                document=document,
                existing_periods_dict=existing_periods_dict,
                stop_processing=stop_processing,
                existing_meta_common_key="sga_to_profit",
                numerator_key="SellingGeneralAndAdministration",
                denominator_key="GrossProfit",
            )
            # if stop_processing["sga_to_profit"] == False:
            #     if (
            #         "SellingGeneralAndAdministration" not in doc_data
            #         or math.isnan(doc_data["SellingGeneralAndAdministration"])
            #         and "GrossProfit" in doc_data
            #         and not math.isnan(doc_data["GrossProfit"])
            #         and doc_data["GrossProfit"] > 0
            #     ):
            #         sga_to_profit = 0
            #     elif (
            #         "GrossProfit" not in doc_data
            #         or math.isnan(doc_data["GrossProfit"])
            #         or doc_data["GrossProfit"] == 0
            #     ):
            #         if "SellingGeneralAndAdministration" not in doc_data or math.isnan(
            #             doc_data["SellingGeneralAndAdministration"]
            #         ):
            #             sga_to_profit = None
            #         else:
            #             sga_to_profit = 1
            #     else:
            #         sga_to_profit = (
            #             doc_data["SellingGeneralAndAdministration"]
            #             / doc_data["GrossProfit"]
            #         )
            #     existing_periods_dict["sga_to_profit"][
            #         str(document["statement_date"])
            #     ] = sga_to_profit

            compute_ratio_meta(
                doc_data=doc_data,
                document=document,
                existing_periods_dict=existing_periods_dict,
                stop_processing=stop_processing,
                existing_meta_common_key="rnd_to_profit",
                numerator_key="ResearchAndDevelopment",
                denominator_key="GrossProfit",
            )
            # if stop_processing["rnd_to_profit"] == False:

            #     if (
            #         "ResearchAndDevelopment" not in doc_data
            #         or math.isnan(doc_data["ResearchAndDevelopment"])
            #         and "GrossProfit" in doc_data
            #         and not math.isnan(doc_data["GrossProfit"])
            #         and doc_data["GrossProfit"] > 0
            #     ):
            #         rnd_to_profit = 0
            #     elif (
            #         "GrossProfit" not in doc_data
            #         or math.isnan(doc_data["GrossProfit"])
            #         or doc_data["GrossProfit"] == 0
            #     ):
            #         if "ResearchAndDevelopment" not in doc_data or math.isnan(
            #             doc_data["ResearchAndDevelopment"]
            #         ):
            #             rnd_to_profit = None
            #         else:
            #             rnd_to_profit = 1
            #     else:
            #         rnd_to_profit = (
            #             doc_data["ResearchAndDevelopment"] / doc_data["GrossProfit"]
            #         )
            #     existing_periods_dict["rnd_to_profit"][
            #         str(document["statement_date"])
            #     ] = rnd_to_profit

            compute_ratio_meta(
                doc_data=doc_data,
                document=document,
                existing_periods_dict=existing_periods_dict,
                stop_processing=stop_processing,
                existing_meta_common_key="depreciation_to_profit",
                numerator_key="DepreciationIncomeStatement",
                denominator_key="GrossProfit",
            )
            # if stop_processing["depreciation_to_profit"] == False:
            #     if (
            #         "DepreciationIncomeStatement" not in doc_data
            #         or math.isnan(doc_data["DepreciationIncomeStatement"])
            #         and "GrossProfit" in doc_data
            #         and not math.isnan(doc_data["GrossProfit"])
            #         and doc_data["GrossProfit"] > 0
            #     ):
            #         depreciation_to_profit = 0
            #     elif (
            #         "GrossProfit" not in doc_data
            #         or math.isnan(doc_data["GrossProfit"])
            #         or doc_data["GrossProfit"] == 0
            #     ):
            #         if "DepreciationIncomeStatement" not in doc_data or math.isnan(
            #             doc_data["DepreciationIncomeStatement"]
            #         ):
            #             depreciation_to_profit = None
            #         else:
            #             depreciation_to_profit = 1
            #     else:
            #         depreciation_to_profit = (
            #             doc_data["DepreciationIncomeStatement"]
            #             / doc_data["GrossProfit"]
            #         )

            #     existing_periods_dict["depreciation_to_profit"][
            #         str(document["statement_date"])
            #     ] = depreciation_to_profit

            compute_ratio_meta(
                doc_data=doc_data,
                document=document,
                existing_periods_dict=existing_periods_dict,
                stop_processing=stop_processing,
                existing_meta_common_key="intrest_payout_to_operating_income",
                numerator_key="InterestExpense",
                denominator_key="OperatingIncome",
            )
            # if stop_processing["intrest_payout_to_operating_income"] == False:
            #     if (
            #         "InterestExpense" not in doc_data
            #         or math.isnan(doc_data["InterestExpense"])
            #         and "OperatingIncome" in doc_data
            #         and not math.isnan(doc_data["OperatingIncome"])
            #         and doc_data["OperatingIncome"] > 0
            #     ):
            #         intrest_payout_to_operating_income = 0
            #     elif (
            #         "OperatingIncome" not in doc_data
            #         or math.isnan(doc_data["OperatingIncome"])
            #         or doc_data["OperatingIncome"] == 0
            #     ):
            #         if "InterestExpense" not in doc_data or math.isnan(
            #             doc_data["InterestExpense"]
            #         ):
            #             intrest_payout_to_operating_income = None
            #         else:
            #             intrest_payout_to_operating_income = 1
            #     else:
            #         intrest_payout_to_operating_income = (
            #             doc_data["InterestExpense"] / doc_data["OperatingIncome"]
            #         )

            #     existing_periods_dict["intrest_payout_to_operating_income"][
            #         str(document["statement_date"])
            #     ] = intrest_payout_to_operating_income

            if stop_processing["net_earnings"] == False:
                if "NetIncome" not in doc_data or math.isnan(doc_data["NetIncome"]):
                    net_earnings = 0
                else:
                    net_earnings = doc_data["NetIncome"]

                existing_periods_dict["net_earnings"][
                    str(document["statement_date"])
                ] = net_earnings

            compute_ratio_meta(
                doc_data=doc_data,
                document=document,
                existing_periods_dict=existing_periods_dict,
                stop_processing=stop_processing,
                existing_meta_common_key="earnings_to_revenue",
                numerator_key="NetIncome",
                denominator_key="TotalRevenue",
            )
            # if stop_processing["earnings_to_revenue"] == False:
            #     if (
            #         "NetIncome" not in doc_data
            #         or math.isnan(doc_data["NetIncome"])
            #         and "OperatingIncome" in doc_data
            #         and not math.isnan(doc_data["TotalRevenue"])
            #         and doc_data["TotalRevenue"] > 0
            #     ):
            #         earnings_to_revenue = 0
            #     elif (
            #         "TotalRevenue" not in doc_data
            #         or math.isnan(doc_data["TotalRevenue"])
            #         or doc_data["TotalRevenue"] == 0
            #     ):
            #         if "NetIncome" not in doc_data or math.isnan(doc_data["NetIncome"]):
            #             earnings_to_revenue = None
            #         else:
            #             earnings_to_revenue = 1
            #     else:
            #         earnings_to_revenue = (
            #             doc_data["NetIncome"] / doc_data["TotalRevenue"]
            #         )

            #     existing_periods_dict["earnings_to_revenue"][
            #         str(document["statement_date"])
            #     ] = earnings_to_revenue

            if stop_processing["eps"] == False:
                if "BasicEPS" not in doc_data or math.isnan(doc_data["BasicEPS"]):
                    eps = 0
                else:
                    eps = doc_data["BasicEPS"]

                existing_periods_dict["eps"][str(document["statement_date"])] = eps

        for key in existing_metas.keys():
            existing_periods = existing_periods_dict[key]
            existing_metric_meta = existing_metas[key]
            existing_metric_meta["periods"] = existing_periods

            # Create dates and values array
            dates = []
            values = []
            sorted_existing_periods_dates = sorted(existing_periods.keys())
            for date in sorted_existing_periods_dates:
                if existing_periods[date] is not None and not math.isnan(
                    existing_periods[date]
                ):
                    dates.append(date)
                    values.append(existing_periods[date])
            existing_metric_meta["dates"] = dates
            existing_metric_meta["values"] = values

            # compute mean, variance and stdev
            existing_metric_meta["mean"] = statistics.mean(values)
            existing_metric_meta["variance"] = statistics.variance(values)
            existing_metric_meta["stdev"] = statistics.stdev(values)

            # assign back variables
            existing_meta_for_timeframe[key] = existing_metric_meta
    except Exception as e:
        print("Error in sga_meta")
        traceback.print_exc()
        raise e


def compute_ratio_meta(
    doc_data,
    document,
    existing_periods_dict,
    stop_processing,
    existing_meta_common_key,
    numerator_key,
    denominator_key,
):
    if stop_processing[existing_meta_common_key] == False:
        if (
            numerator_key not in doc_data
            or math.isnan(doc_data[numerator_key])
            and denominator_key in doc_data
            and not math.isnan(doc_data[denominator_key])
            and doc_data[denominator_key] > 0
        ):
            ratio = 0
        elif (
            denominator_key not in doc_data
            or math.isnan(doc_data[denominator_key])
            or doc_data[denominator_key] == 0
        ):
            if numerator_key not in doc_data or math.isnan(doc_data[numerator_key]):
                ratio = None
            else:
                ratio = 1
        else:
            ratio = doc_data[numerator_key] / doc_data[denominator_key]
        existing_periods_dict[existing_meta_common_key][
            str(document["statement_date"])
        ] = ratio
