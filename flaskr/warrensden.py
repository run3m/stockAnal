import functools
import csv
import io
import traceback
from flask import (
    Blueprint,
    flash,
    current_app,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
)
from pymongo import UpdateOne
from werkzeug.security import check_password_hash, generate_password_hash

from .models.statement import StatementTimeFrame

from .db_config import get_db
import requests
import os
from datetime import datetime
import requests_cache

from . import models
import json
import yfinance as yf
import math
from .util.cached_limiter_session import session
from .util import warren_meta

bp = Blueprint("warren", __name__, url_prefix="/warren")


@bp.route("/getSheetsForStock", methods=["POST"])
def getSheetsForStock():
    try:
        query_params = request.args

        db = get_db()["myDatabase"]
        # Get all rows from warren_fetch_status where full_fetched : false
        warren_fetch_status_collection = db["warren_fetch_status"]
        stock = db["nifty500"].find_one({"symbol": query_params.get("symbol")})
        if stock is None:
            return (
                jsonify(
                    {"status": "fail", "error": "No stock exists with given symbol"}
                ),
                400,
            )

        warren_unfetched = warren_fetch_status_collection.find({"_id": stock["_id"]})

        stock_ticker = yf.Ticker(f"{stock['symbol']}.NS", session=session)
        statements_collection = db["statements"]

        # For each stock in warren_fetch_status, fetch : income, balance sheet, cashflow(4 years, 5 quaters)
        statement_data = []

        stock_statements = list(statements_collection.find({"stock_id": stock["_id"]}))
        # for each stock get the latest year and quater. If the current year, quater is not the current one then make request for them.
        existing_statements_yearly = sorted(
            [
                statement
                for statement in stock_statements
                if statement["time_frame"] == StatementTimeFrame.YEARLY
            ],
            key=lambda x: x["year"],
            reverse=True,
        )

        existing_statements_quaterly = sorted(
            [
                statement
                for statement in stock_statements
                if statement["time_frame"] == StatementTimeFrame.QUARTERLY
            ],
            key=lambda x: (-x["year"], -x["quarter"]),
        )
        income_statement_yearly = balance_sheet_yearly = cash_flow_statement_yearly = (
            income_statement_quaterly
        ) = balance_sheet_quaterly = cash_flow_statement_quaterly = None
        if should_fetch_data(existing_statements_yearly, StatementTimeFrame.YEARLY):
            # Yearly statements
            # Added get_new_statements function to fetch only new statement. Check if logic is working correctly and apply to all statements.
            income_statement_yearly = stock_ticker.get_income_stmt(
                as_dict=True, freq=StatementTimeFrame.YEARLY.value
            )
            income_statement_inserts = get_new_statements(
                income_statement_yearly,
                existing_statements_yearly,
                models.StatementType.INCOME_STATEMENT,
            )
            statement_data.extend(
                create_statement_documents(
                    stock=stock,
                    statement_type=models.StatementType.INCOME_STATEMENT,
                    freq=StatementTimeFrame.YEARLY,
                    data=income_statement_inserts,
                )
            )
            income_statement_yearly = {
                str(key): value for key, value in income_statement_yearly.items()
            }

            balance_sheet_yearly = stock_ticker.get_balance_sheet(
                as_dict=True, freq=StatementTimeFrame.YEARLY.value
            )
            balance_sheet_inserts = get_new_statements(
                balance_sheet_yearly,
                existing_statements_yearly,
                models.StatementType.BALANCE_SHEET,
            )
            statement_data.extend(
                create_statement_documents(
                    stock=stock,
                    statement_type=models.StatementType.BALANCE_SHEET,
                    freq=StatementTimeFrame.YEARLY,
                    data=balance_sheet_inserts,
                )
            )
            balance_sheet_yearly = {
                str(key): value for key, value in balance_sheet_yearly.items()
            }

            cash_flow_statement_yearly = stock_ticker.get_cash_flow(
                as_dict=True, freq=StatementTimeFrame.YEARLY.value
            )
            cash_flow_inserts = get_new_statements(
                cash_flow_statement_yearly,
                existing_statements_yearly,
                models.StatementType.CASHFLOW_STATEMENT,
            )
            statement_data.extend(
                create_statement_documents(
                    stock=stock,
                    statement_type=models.StatementType.CASHFLOW_STATEMENT,
                    freq=StatementTimeFrame.YEARLY,
                    data=cash_flow_inserts,
                )
            )
            cash_flow_statement_yearly = {
                str(key): value for key, value in cash_flow_statement_yearly.items()
            }

        if should_fetch_data(
            existing_statements_quaterly, StatementTimeFrame.QUARTERLY
        ):
            # Quaterly statements
            income_statement_quaterly = stock_ticker.get_income_stmt(
                as_dict=True, freq=StatementTimeFrame.QUARTERLY.value
            )
            income_statement_inserts = get_new_statements(
                income_statement_quaterly,
                existing_statements_quaterly,
                models.StatementType.INCOME_STATEMENT,
            )
            statement_data.extend(
                create_statement_documents(
                    stock=stock,
                    statement_type=models.StatementType.INCOME_STATEMENT,
                    freq=StatementTimeFrame.QUARTERLY,
                    data=income_statement_inserts,
                )
            )
            income_statement_quaterly = {
                str(key): value for key, value in income_statement_quaterly.items()
            }

            balance_sheet_quaterly = stock_ticker.get_balance_sheet(
                as_dict=True, freq=StatementTimeFrame.QUARTERLY.value
            )
            balance_sheet_inserts = get_new_statements(
                balance_sheet_quaterly,
                existing_statements_quaterly,
                models.StatementType.BALANCE_SHEET,
            )
            statement_data.extend(
                create_statement_documents(
                    stock=stock,
                    statement_type=models.StatementType.BALANCE_SHEET,
                    freq=StatementTimeFrame.QUARTERLY,
                    data=balance_sheet_inserts,
                )
            )
            balance_sheet_quaterly = {
                str(key): value for key, value in balance_sheet_quaterly.items()
            }

            cash_flow_statement_quaterly = stock_ticker.get_cash_flow(
                as_dict=True, freq=StatementTimeFrame.QUARTERLY.value
            )
            cash_flow_inserts = get_new_statements(
                cash_flow_statement_quaterly,
                existing_statements_quaterly,
                models.StatementType.CASHFLOW_STATEMENT,
            )
            statement_data.extend(
                create_statement_documents(
                    stock=stock,
                    statement_type=models.StatementType.CASHFLOW_STATEMENT,
                    freq=StatementTimeFrame.QUARTERLY,
                    data=cash_flow_inserts,
                )
            )
            cash_flow_statement_quaterly = {
                str(key): value for key, value in cash_flow_statement_quaterly.items()
            }

        # Fetch each of the sheet and store in db(4 at a time, 5 at a time or 9 at a time.)
        if len(statement_data) > 0:
            inserted_statements = statements_collection.insert_many(statement_data)
            print(
                "Inserted Document count : ",
                len(inserted_statements.inserted_ids),
                " Statements list count : ",
                len(statement_data),
            )

        updated_status = warren_fetch_status_collection.update_one(
            {"_id": stock["_id"]}, {"$set": {"full_fetched": True}}
        )
        print(updated_status.modified_count)

        return {
            "income_statement_yearly": income_statement_yearly,
            "balance_sheet_yearly": balance_sheet_yearly,
            "cash_flow_statement_yearly": cash_flow_statement_yearly,
            "income_statement_quaterly": income_statement_quaterly,
            "balance_sheet_quaterly": balance_sheet_quaterly,
            "cash_flow_statement_quaterly": cash_flow_statement_quaterly,
        }
        # return {"income_statement_yearly" : income_statement_yearly}
        # After fetch for each statement is done change fetch status of that sheet to true
    except Exception as e:
        traceback.print_exc()
        return (
            jsonify(
                {
                    "status": "fail",
                    "error": f"An exception occured while processing : {str(e)}",
                    "trace": traceback.format_exc(),
                }
            ),
            400,
        )


def create_statement_documents(
    stock, statement_type: models.StatementType, freq, data: dict
) -> list[models.Statement]:
    documents: list[models.Statement] = []
    for key, value in data.items():
        year = int(key.year)
        document: models.Statement = None
        if freq == StatementTimeFrame.QUARTERLY:
            quarter = math.ceil(int(key.month) / 3)
            document: models.Statement = models.Statement(
                stock_id=stock["_id"],
                ticker=stock["symbol"],
                statement_type=statement_type,
                year=year,
                quarter=quarter,
                time_frame=freq,
                data=value,
                statement_date=key.to_pydatetime(),
                date=datetime.now(),
            )
        else:
            document: models.Statement = models.Statement(
                stock_id=stock["_id"],
                ticker=stock["symbol"],
                statement_type=statement_type,
                year=year,
                time_frame=freq,
                data=value,
                statement_date=key.to_pydatetime(),
                date=datetime.now(),
            )
        if document is not None:
            documents.append(document.model_dump(exclude_none=True))
    return documents


def get_new_statements(fetched_data, existing_statement, statement_type):
    to_be_inserted = {}
    filtered_existing_dates = [
        statement["statement_date"]
        for statement in existing_statement
        if statement["statement_type"] == statement_type
    ]
    for key, value in fetched_data.items():
        if key.to_pydatetime() in filtered_existing_dates:
            # we can return directly when we get the keys(date) in sorted order. or else we'll have to continue the loop.
            return to_be_inserted
        to_be_inserted[key] = value

    return to_be_inserted


def should_fetch_data(
    existing_statements: list[models.Statement], time_frame: StatementTimeFrame
) -> bool:
    if len(existing_statements) == 0:
        return True

    latest_statement = existing_statements[0]
    cur_year = datetime.now().year
    cur_month = datetime.now().month
    if time_frame == StatementTimeFrame.YEARLY:
        if cur_year - latest_statement["year"] > 1 or (
            cur_year - latest_statement["year"] == 1 and cur_month > 3
        ):
            return True
    else:
        current_quater = math.ceil((cur_month) / 3)
        if cur_year > latest_statement["year"]:
            # current year is greater than lastest_statement.year
            if (current_quater + 4) - latest_statement["quarter"] >= 2:
                return True
        elif current_quater - latest_statement["quarter"] >= 2:
            # here current year and lastest_statement.year are same.
            return True

    return False


@bp.route("/warren_fetch", methods=["POST"])
def fetchStocks():
    try:
        db = get_db()["myDatabase"]
        # Get all rows from warren_fetch_status where full_fetched : false
        warren_fetch_status_collection = db["warren_fetch_status"]
        warren_unfetched = warren_fetch_status_collection.find({"full_fetched": False})

        response = {}
        for stock in warren_unfetched:
            stock = db["nifty500"].find_one({"_id": stock["stock_id"]})
            if stock is None:
                response[stock["symbol"]] = None

            stock_ticker = yf.Ticker(f"{stock['symbol']}.NS", session=session)
            statements_collection = db["statements"]

            # For each stock in warren_fetch_status, fetch : income, balance sheet, cashflow(4 years, 5 quaters)
            statement_data = []

            stock_statements = list(
                statements_collection.find({"stock_id": stock["_id"]})
            )
            # for each stock get the latest year and quater. If the current year, quater is not the current one then make request for them.
            existing_statements_yearly = sorted(
                [
                    statement
                    for statement in stock_statements
                    if statement["time_frame"] == StatementTimeFrame.YEARLY
                ],
                key=lambda x: x["year"],
                reverse=True,
            )

            existing_statements_quaterly = sorted(
                [
                    statement
                    for statement in stock_statements
                    if statement["time_frame"] == StatementTimeFrame.QUARTERLY
                ],
                key=lambda x: (-x["year"], -x["quarter"]),
            )
            income_statement_yearly = balance_sheet_yearly = (
                cash_flow_statement_yearly
            ) = income_statement_quaterly = balance_sheet_quaterly = (
                cash_flow_statement_quaterly
            ) = None
            if should_fetch_data(existing_statements_yearly, StatementTimeFrame.YEARLY):
                # Yearly statements
                # Added get_new_statements function to fetch only new statement. Check if logic is working correctly and apply to all statements.
                income_statement_yearly = stock_ticker.get_income_stmt(
                    as_dict=True, freq=StatementTimeFrame.YEARLY.value
                )
                income_statement_inserts = get_new_statements(
                    income_statement_yearly,
                    existing_statements_yearly,
                    models.StatementType.INCOME_STATEMENT,
                )
                statement_data.extend(
                    create_statement_documents(
                        stock=stock,
                        statement_type=models.StatementType.INCOME_STATEMENT,
                        freq=StatementTimeFrame.YEARLY,
                        data=income_statement_inserts,
                    )
                )
                income_statement_yearly = {
                    str(key): value for key, value in income_statement_yearly.items()
                }

                balance_sheet_yearly = stock_ticker.get_balance_sheet(
                    as_dict=True, freq=StatementTimeFrame.YEARLY.value
                )
                balance_sheet_inserts = get_new_statements(
                    balance_sheet_yearly,
                    existing_statements_yearly,
                    models.StatementType.BALANCE_SHEET,
                )
                statement_data.extend(
                    create_statement_documents(
                        stock=stock,
                        statement_type=models.StatementType.BALANCE_SHEET,
                        freq=StatementTimeFrame.YEARLY,
                        data=balance_sheet_inserts,
                    )
                )
                balance_sheet_yearly = {
                    str(key): value for key, value in balance_sheet_yearly.items()
                }

                cash_flow_statement_yearly = stock_ticker.get_cash_flow(
                    as_dict=True, freq=StatementTimeFrame.YEARLY.value
                )
                cash_flow_inserts = get_new_statements(
                    cash_flow_statement_yearly,
                    existing_statements_yearly,
                    models.StatementType.CASHFLOW_STATEMENT,
                )
                statement_data.extend(
                    create_statement_documents(
                        stock=stock,
                        statement_type=models.StatementType.CASHFLOW_STATEMENT,
                        freq=StatementTimeFrame.YEARLY,
                        data=cash_flow_inserts,
                    )
                )
                cash_flow_statement_yearly = {
                    str(key): value for key, value in cash_flow_statement_yearly.items()
                }

            if should_fetch_data(
                existing_statements_quaterly, StatementTimeFrame.QUARTERLY
            ):
                # Quaterly statements
                income_statement_quaterly = stock_ticker.get_income_stmt(
                    as_dict=True, freq=StatementTimeFrame.QUARTERLY.value
                )
                income_statement_inserts = get_new_statements(
                    income_statement_quaterly,
                    existing_statements_quaterly,
                    models.StatementType.INCOME_STATEMENT,
                )
                statement_data.extend(
                    create_statement_documents(
                        stock=stock,
                        statement_type=models.StatementType.INCOME_STATEMENT,
                        freq=StatementTimeFrame.QUARTERLY,
                        data=income_statement_inserts,
                    )
                )
                income_statement_quaterly = {
                    str(key): value for key, value in income_statement_quaterly.items()
                }

                balance_sheet_quaterly = stock_ticker.get_balance_sheet(
                    as_dict=True, freq=StatementTimeFrame.QUARTERLY.value
                )
                balance_sheet_inserts = get_new_statements(
                    balance_sheet_quaterly,
                    existing_statements_quaterly,
                    models.StatementType.BALANCE_SHEET,
                )
                statement_data.extend(
                    create_statement_documents(
                        stock=stock,
                        statement_type=models.StatementType.BALANCE_SHEET,
                        freq=StatementTimeFrame.QUARTERLY,
                        data=balance_sheet_inserts,
                    )
                )
                balance_sheet_quaterly = {
                    str(key): value for key, value in balance_sheet_quaterly.items()
                }

                cash_flow_statement_quaterly = stock_ticker.get_cash_flow(
                    as_dict=True, freq=StatementTimeFrame.QUARTERLY.value
                )
                cash_flow_inserts = get_new_statements(
                    cash_flow_statement_quaterly,
                    existing_statements_quaterly,
                    models.StatementType.CASHFLOW_STATEMENT,
                )
                statement_data.extend(
                    create_statement_documents(
                        stock=stock,
                        statement_type=models.StatementType.CASHFLOW_STATEMENT,
                        freq=StatementTimeFrame.QUARTERLY,
                        data=cash_flow_inserts,
                    )
                )
                cash_flow_statement_quaterly = {
                    str(key): value
                    for key, value in cash_flow_statement_quaterly.items()
                }

            # Fetch each of the sheet and store in db(4 at a time, 5 at a time or 9 at a time.)
            if len(statement_data) > 0:
                inserted_statements = statements_collection.insert_many(statement_data)
                print(
                    f"Inserted Document count for stock {stock['symbol']} : ",
                    len(inserted_statements.inserted_ids),
                    " Statements list count : ",
                    len(statement_data),
                )

            updated_status = warren_fetch_status_collection.update_one(
                {"stock_id": stock["_id"]}, {"$set": {"full_fetched": True}}
            )
            print(
                f"Updated fetch status for {stock['symbol']}",
                updated_status.modified_count,
            )

            if stock["symbol"] in response:
                print(
                    f"Symbol {stock['symbol']} already in response object. Dulplicating to {stock['symbol']}_copy"
                )
                stock["symbol"] = stock["symbol"] + "_copy"
            response[stock["symbol"]] = {
                "income_statement_yearly": income_statement_yearly,
                "balance_sheet_yearly": balance_sheet_yearly,
                "cash_flow_statement_yearly": cash_flow_statement_yearly,
                "income_statement_quaterly": income_statement_quaterly,
                "balance_sheet_quaterly": balance_sheet_quaterly,
                "cash_flow_statement_quaterly": cash_flow_statement_quaterly,
            }

        return response

    except Exception as e:
        traceback.print_exc()
        return (
            jsonify(
                {
                    "status": "fail",
                    "error": f"An exception occured while processing : {str(e)}",
                    "trace": traceback.format_exc(),
                }
            ),
            400,
        )


@bp.route("/resetFetchStatus", methods=["POST"])
def resetFetchStatus():
    try:
        db = get_db()["myDatabase"]
        nifty500 = db["nifty500"]

        nifty500_records = nifty500.find()

        warren_status_records = [
            models.WarrenFetchStatus(stock_id=nifty500_record["_id"]).model_dump(
                exclude_none=True
            )
            for nifty500_record in nifty500_records
        ]

        warren_fetch_status_collection = db["warren_fetch_status"]

        # Deleting all records from warren_fetch_status before adding them again.
        warren_fetch_status_collection.delete_many({})

        # Insert all records into warren_fetch_status
        warren_fetch_status_insert_data = warren_fetch_status_collection.insert_many(
            warren_status_records
        )

        return {
            "staus": "success",
            "inserted_records": [
                str(inserted_id)
                for inserted_id in warren_fetch_status_insert_data.inserted_ids
            ],
        }
    except Exception as e:
        print("Error occured in resetFetchStatus : ", e)
        return {"status": "error", "error": e}


@bp.route("/propertyStatementMapping", methods=["GET", "POST"])
def property_sheet_mapping():
    db = get_db()["myDatabase"]
    if request.method == "GET":
        print("get props")
        property_statement_mapping_collection = db["property_statement_mapping"]
        return property_statement_mapping_collection.find({})[0]["mapping"]
    elif request.method == "POST":
        statements_collection = db["statements"]
        statements = statements_collection.find()
        statement_types = {
            "INCOME_STATEMENT": 0,
            "BALANCE_SHEET": 0,
            "CASHFLOW_STATEMENT": 0,
        }
        no_new_fields = False
        fields = {}
        for statement in statements:
            if statement_types[statement["statement_type"]] >= 5:
                if all(value >= 5 for value in statement_types.values()):
                    print(
                        f"Each statement is seen atleast 5 times, {statement_types.items()}"
                    )
                    break
                continue

            statement_types[statement["statement_type"]] += 1

            data = statement["data"]
            for key in data.keys():
                if key not in fields:
                    fields[key] = statement["statement_type"]
                elif fields[key] != statement["statement_type"]:
                    print(
                        f"{key} already set for {fields[key]}, now also found for {statement['statement_type']}"
                    )

        property_statement_mapping_collection = db["property_statement_mapping"]
        property_statement_mapping_collection.delete_many({})
        property_statement_mapping_collection.insert_one({"mapping": fields})
        return fields


@bp.route("/runAnalysis", methods=["POST"])
def runAnalysis():
    try:
        db = get_db()["myDatabase"]
        # get statements collection
        statements_collection = db["statements"]

        # aggregrate pipeline for grouping by time_frame, statement_type and ticker. And sorting by statement_date
        pipeline = [
            # {"$match": {"ticker": "COFORGE"}},
            {
                "$group": {
                    "_id": {
                        "time_frame": "$time_frame",
                        "statement_type": "$statement_type",
                        "ticker": "$ticker",
                    },
                    "count": {"$sum": 1},
                    "documents": {
                        "$push": {
                            "id": "$_id",
                            "stock_id": "$stock_id",
                            "ticker": "$ticker",
                            "statement_type": "$statement_type",
                            "year": "$year",
                            "quarter": "$quarter",
                            "time_frame": "$time_frame",
                            "data": "$data",
                            "statement_date": "$statement_date",
                            "date": "$date",
                        }
                    },
                },
            },
            {
                "$addFields": {
                    "documents": {
                        "$sortArray": {
                            "input": "$documents",
                            "sortBy": {"statement_date": -1},
                        }
                    }
                }
            },
        ]
        # fetch statements grouped by fields
        stock_statements = statements_collection.aggregate(pipeline)

        output = []

        # fetch existing stock meta details we are storing.
        stock_meta_collection = db["stock_meta"]
        stocks_meta: list[models.StockMeta] = [
            models.StockMeta(**doc) for doc in stock_meta_collection.find()
        ]
        stocks_meta_dict: dict[str, models.StockMeta] = {
            stock_meta.ticker: stock_meta for stock_meta in stocks_meta
        }
        # for stock_meta in stocks_meta:
        #     stocks_meta_dict[stock_meta["ticker"]] = stock_meta

        updated_meta_stock_tickers = set()
        for statement in stock_statements:
            try:
                # This is just test check for only income statements, remove later
                if (
                    statement["_id"]["statement_type"]
                    == models.StatementType.INCOME_STATEMENT.value
                ):
                    # check if stock meta details for a stock already exists or not.
                    stock_id = None
                    if statement["_id"]["ticker"] not in stocks_meta_dict:
                        stock_meta = models.StockMeta(
                            ticker=statement["_id"]["ticker"], quarterly={}, yearly={}
                        )
                        # {
                        #     "ticker": statement["_id"]["ticker"],
                        #     "quarterly": {},
                        #     "yearly": {},
                        # }
                    else:
                        stock_meta = stocks_meta_dict[statement["_id"]["ticker"]]
                        stock_id = stock_meta.stock_id

                    # Income statement checks
                    if (
                        statement["_id"]["statement_type"]
                        == models.StatementType.INCOME_STATEMENT.value
                    ):
                        # gross_profit_meta
                        # warren_meta.gross_profit_meta(statement, stock_meta, stock_id)

                        # SGA_meta
                        # warren_meta.sga_meta(statement, stock_meta)

                        # R&D
                        # warren_meta.rnd_meta(statement, stock_meta)

                        # Dep
                        # warren_meta.depreciation_meta(statement, stock_meta)
                        warren_meta.common_meta(statement, stock_meta, stock_id)
                    if stock_meta.stock_id is not None:
                        stocks_meta_dict[stock_meta.ticker] = stock_meta
                        updated_meta_stock_tickers.add(stock_meta.ticker)
                        # stock_meta_collection.update_one(
                        #     {"stock_id": stock_meta["stock_id"]},
                        #     {"$set": stock_meta},
                        #     upsert=True,
                        # )

                    output_documents = [
                        {
                            "ticker": document["ticker"],
                            "statement_type": document["statement_type"],
                            "year": document["year"],
                            "quarter": (
                                document["quarter"] if "quarter" in document else None
                            ),
                            "time_frame": document["time_frame"],
                            "statement_date": document["statement_date"],
                            "date": document["date"],
                        }
                        for document in statement["documents"]
                    ]
                    statement_copy = statement.copy()
                    statement_copy["documents"] = output_documents
                    output.append(statement_copy)
            except Exception as e:
                print(
                    "Error in /runAnalysis for loop : for statement in stock_statements"
                )
                traceback.print_exc()
                continue

        bulk_operations = [
            UpdateOne(
                {"stock_id": getattr(stocks_meta_dict[ticker], "stock_id")},
                {
                    "$set": stocks_meta_dict[ticker].model_dump(
                        by_alias=True, exclude_defaults=True
                    )
                },
                upsert=True,
            )
            for ticker in updated_meta_stock_tickers
        ]

        if len(bulk_operations) > 0:
            # Perform the bulk write operation
            result = stock_meta_collection.bulk_write(bulk_operations)
            print(result)

        return {"statements": output}
    except Exception as e:
        print("Error in /runAnalysis")
        traceback.print_exc()
        return {"Error": e}


def update_nifty_500():
    try:
        print("s", datetime.now())
        db = get_db()["myDatabase"]
        nifty500 = db["nifty500"]
        csv_reader = None
        print("e", datetime.now())
        if request.method == "POST":
            print("s0", datetime.now())
            if "file" not in request.files:
                raise Exception("Please attach file")

            file = request.files["file"]
            csv_reader = csv.DictReader(io.StringIO(file.read().decode("utf-8")))
            print("e0", datetime.now())
            # csv_reader = [i for i in csv_reader];
        else:
            headers_collection = db["headers"]
            headers_doc = headers_collection.find_one({"type": "nifty500"})
            response = requests.get(
                current_app.config["URLS"]["nifty_500"], headers=headers_doc["headers"]
            )
            if response.status_code == 200:
                # Create a list to store the parsed CSV data as dictionaries
                # Parse the CSV data
                csv_content = response.text
                csv_reader = csv.DictReader(csv_content.splitlines())
            else:
                print(
                    f"Failed to download the file. Status code: {response.status_code}"
                )
                raise Exception("Unable to download file.")

        new_docs = []
        print(csv_reader)

        print("s9", datetime.now())
        all_existing = nifty500.find({}, {"symbol": 1})
        print("e9", datetime.now())

        print("s10", datetime.now())
        all_existing_symbols = [doc["symbol"] for doc in all_existing]

        old_symbols = [
            row["Symbol"] for row in csv_reader if row["Symbol"] in all_existing_symbols
        ]
        new_docs = [
            {
                "name": row["Company Name"],
                "industry": row["Industry"],
                "symbol": row["Symbol"],
                "created_on": datetime.now(),
            }
            for row in csv_reader
            if row["Symbol"] not in all_existing_symbols
        ]
        print("e10", datetime.now())

        if len(old_symbols) > 0:
            print("s1", datetime.now())
            nifty500.update_many(
                {"symbol": {"$in": old_symbols}},
                {"$set": {"updated_on": datetime.now()}},
            )
            print("e1", datetime.now())
        if len(new_docs) > 0:
            print("s2", datetime.now())
            nifty500.insert_many(new_docs)
            print("e2", datetime.now())

        # if not os.path.exists('./data'):
        #     os.makedirs('./data')
        # with open('./data/ind_nifty500list.csv', 'wb') as file:
        #     file.write(response.content)
        # print('File downloaded successfully.')
        return {"status": "success"}
    except Exception as e:
        print(f"Error occured in update_nifty_500 : {e}")
        traceback.print_exc()
        return {"status": "failed", "error": e}
