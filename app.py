import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os
from dotenv import load_dotenv
import sentry_sdk
import logging

# استيراد الوحدات النمطية الخاصة بالمشروع
from utils import setup_logging, prepare_arabic_text, load_css, format_currency
from db_manager import get_db_manager
from calculations import calculate_primary_yield, analyze_secondary_sale
from cbe_scraper import fetch_data_from_cbe
import constants as C

# إعدادات أولية
setup_logging(level=logging.WARNING)
load_dotenv()

# --- تهيئة Sentry لمراقبة التطبيق ---
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        environment="production-streamlit",
    )


def display_auction_results(title: str, info: str, df: pd.DataFrame):
    if not df.empty:
        session_date = df[C.SESSION_DATE_COLUMN_NAME].iloc[0]
        if pd.isna(session_date):
            session_date_str = prepare_arabic_text("تاريخ غير محدد")
        else:
            session_date_str = str(session_date)

        st.markdown(
            f"<h3 style='text-align: center; color: #ffc107;'>{prepare_arabic_text(f'{title} - {session_date_str}')}</h3>",
            unsafe_allow_html=True,
        )

        info_with_note = f"{info}<br><small>للشراء يتطلب التواجد في البنك قبل الساعة 10 صباحًا في يوم العطاء.</small>"
        st.markdown(
            f"""
            <div style="text-align: center; padding: 0.75rem; background-color: rgba(38, 39, 48, 0.5); border-radius: 0.5rem; border: 1px solid #3c4049; margin-top: 10px; margin-bottom: 20px;">
                🗓️ {prepare_arabic_text(info_with_note)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        df_sorted = df.sort_values(by=C.TENOR_COLUMN_NAME)
        if len(df_sorted) > 0:
            cols = st.columns(len(df_sorted))
            for i, (_, tenor_data) in enumerate(df_sorted.iterrows()):
                with cols[i]:
                    label = prepare_arabic_text(
                        f"أجل {tenor_data[C.TENOR_COLUMN_NAME]} يوم"
                    )
                    value = f"{tenor_data[C.YIELD_COLUMN_NAME]:.3f}%"
                    card_html = f"""
                    <div style="background-color: #2c3e50; border: 1px solid #4a6fa5; border-radius: 5px; padding: 15px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);">
                        <p style="font-size: 1.1rem; color: #bdc3c7; margin: 0 0 8px 0; font-weight: 500;">{label}</p>
                        <p style="font-size: 2rem; font-weight: 700; color: #ffffff; margin: 0; line-height: 1.1;">{value}</p>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)


def main():
    st.set_page_config(
        layout="wide",
        page_title=prepare_arabic_text("حاسبة أذون الخزانة"),
        page_icon="🏦",
    )

    st.markdown(
        """
        <head>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap">
        </head>
        """,
        unsafe_allow_html=True,
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_file_path = os.path.join(current_dir, "css", "style.css")
    load_css(css_file_path)

    db_manager = get_db_manager()

    if "primary_results" not in st.session_state:
        st.session_state.primary_results = None
    if "secondary_results" not in st.session_state:
        st.session_state.secondary_results = None

    if "df_data" not in st.session_state:
        st.session_state.df_data, st.session_state.last_update = (
            db_manager.load_latest_data()
        )
    if "historical_df" not in st.session_state:
        st.session_state.historical_df = db_manager.load_all_historical_data()

    data_df = st.session_state.df_data
    last_update_text = st.session_state.last_update
    historical_df = st.session_state.historical_df

    st.markdown(
        f"""
    <div class="centered-header" style="background-color: #343a40; padding: 20px 10px; border-radius: 15px; margin-bottom: 1rem; box-shadow: 0 4px 12px 0 rgba(0,0,0,0.1);">
        <h1 style="color: #ffffff; margin: 0; font-size: 2.5rem;">{prepare_arabic_text(C.APP_TITLE)}</h1>
        <p style="color: #aab8c2; margin: 10px 0 0 0; font-size: 1.1rem;">{prepare_arabic_text(C.APP_HEADER)}</p>
        <div style="margin-top: 15px; font-size: 0.9rem; color: #adb5bd;">
            {prepare_arabic_text("صُمم وبُرمج بواسطة")}
            <span style="font-weight: bold; color: #00bfff;">{C.AUTHOR_NAME}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    top_col1, top_col2 = st.columns([2, 1], gap="large")

    with top_col1:
        with st.container(border=True):
            st.subheader(prepare_arabic_text("📊 أحدث العوائد المعتمدة"), anchor=False)
            st.divider()

            if not data_df.empty and "البيانات الأولية" not in str(last_update_text):
                try:
                    sunday_df = data_df[data_df[C.TENOR_COLUMN_NAME].isin([91, 273])]
                    thursday_df = data_df[data_df[C.TENOR_COLUMN_NAME].isin([182, 364])]

                    display_auction_results(
                        "عطاء الخميس",
                        "آجال (6 أشهر و 12 شهر) - التنفيذ الفعلي يوم الثلاثاء التالي.",
                        thursday_df,
                    )

                    st.divider()

                    display_auction_results(
                        "عطاء الأحد",
                        "آجال (3 أشهر و 9 أشهر) - التنفيذ الفعلي يوم الثلاثاء التالي.",
                        sunday_df,
                    )

                    st.divider()

                except Exception as e:
                    logging.exception("Error displaying auction results.")
                    if sentry_dsn:
                        sentry_sdk.capture_exception(e)
                    st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
            else:
                st.info(
                    prepare_arabic_text("في انتظار ورود البيانات من البنك المركزي...")
                )

    with top_col2:
        with st.container(border=True):
            st.subheader(prepare_arabic_text("📡 حالة البيانات"), anchor=False)

            date_str, time_str = (
                last_update_text
                if isinstance(last_update_text, tuple)
                else (last_update_text, None)
            )

            st.markdown(
                f"""
            <div style="text-align: center; padding: 10px; border: 1px solid #495057; border-radius: 10px; background-color: #212529; margin-bottom: 1rem;">
                <p style="font-size: 0.9rem; margin-bottom: 5px; color: #adb5bd;">آخر تحديث للبيانات</p>
                <p style="font-size: 1.4rem; font-weight: bold; color: #ffffff; margin: 0;">{prepare_arabic_text(str(date_str))}</p>
                {f'<p style="font-size: 1.1rem; color: #adb5bd; margin: 0;">{prepare_arabic_text(str(time_str))}</p>' if time_str else ''}
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button(
                " تحديث البيانات الآن 🔄",
                type="primary",
                use_container_width=True,
                help="قد تستغرق هذه العملية دقيقة أو اثنتين.",
            ):
                progress_bar = st.progress(0, text="...بدء عملية التحديث")
                status_text = st.empty()

                def update_progress(status: str):
                    progress_map = {
                        "إعداد المتصفح": 10,
                        "الاتصال بموقع البنك": 30,
                        "تحليل المحتوى": 60,
                        "العثور على بيانات جديدة": 80,
                        "اكتمل": 100,
                        "محدثة بالفعل": 100,
                    }
                    progress_value = 0
                    progress_key = status
                    for key, value in progress_map.items():
                        if key in status:
                            progress_value = value
                            break
                    status_text.info(f"الحالة: {progress_key}")
                    progress_bar.progress(progress_value, text=progress_key)

                try:
                    fetch_data_from_cbe(db_manager, status_callback=update_progress)
                    progress_bar.progress(100, text="اكتمل التحديث!")
                    st.success("تم تحديث البيانات بنجاح!")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    logging.exception("Data fetch from CBE failed during button click.")
                    if sentry_dsn:
                        sentry_sdk.capture_exception(e)
                    st.error(f"فشل التحديث: {e}")

            st.link_button(
                "🔗 فتح موقع البنك المركزي", C.CBE_DATA_URL, use_container_width=True
            )

    st.divider()
    st.header(prepare_arabic_text(C.PRIMARY_CALCULATOR_TITLE))

    col_form_main, col_results_main = st.columns(2, gap="large")

    with col_form_main:
        with st.container(border=True):
            st.subheader(prepare_arabic_text("1. أدخل بيانات الاستثمار"), anchor=False)

            investment_amount_main = st.number_input(
                prepare_arabic_text("المبلغ المراد استثماره (القيمة الإسمية)"),
                min_value=C.MIN_T_BILL_AMOUNT,
                value=C.MIN_T_BILL_AMOUNT,
                step=C.T_BILL_AMOUNT_STEP,
                help="أدخل القيمة التي ستحصل عليها في نهاية المدة، وعادة ما تكون من مضاعفات 25,000 جنيه.",
            )

            options = (
                sorted(data_df[C.TENOR_COLUMN_NAME].unique())
                if not data_df.empty
                else [91, 182, 273, 364]
            )

            def get_yield_for_tenor(tenor):
                if not data_df.empty:
                    yield_row = data_df[data_df[C.TENOR_COLUMN_NAME] == tenor]
                    if not yield_row.empty:
                        return yield_row[C.YIELD_COLUMN_NAME].iloc[0]
                return None

            formatted_options = []
            for tenor in options:
                yield_val = get_yield_for_tenor(tenor)
                if yield_val is not None:
                    formatted_options.append(
                        f"{tenor} {prepare_arabic_text('يوم')} - ({yield_val:.3f}%)"
                    )
                else:
                    formatted_options.append(f"{tenor} {prepare_arabic_text('يوم')}")

            selected_option = st.selectbox(
                prepare_arabic_text("اختر مدة الاستحقاق"),
                formatted_options,
                key="main_tenor_formatted",
                help="اختر مدة الإذن التي ترغب في حساب عائدها.",
            )
            selected_tenor_main = (
                int(selected_option.split(" ")[0]) if selected_option else None
            )
            tax_rate_main = st.number_input(
                prepare_arabic_text("نسبة الضريبة على الأرباح (%)"),
                min_value=0.0,
                max_value=100.0,
                value=C.DEFAULT_TAX_RATE_PERCENT,
                step=0.5,
                format="%.1f",
                help="ضريبة الأرباح على أذون الخزانة، حالياً 20%.",
            )

            if st.button(
                prepare_arabic_text("احسب العائد الآن"),
                use_container_width=True,
                type="primary",
            ):
                if selected_tenor_main is not None:
                    yield_rate = get_yield_for_tenor(selected_tenor_main)
                    if yield_rate is not None and not data_df.empty:
                        results_dict = calculate_primary_yield(
                            investment_amount_main,
                            yield_rate,
                            selected_tenor_main,
                            tax_rate_main,
                        )
                        if not results_dict.get("error"):
                            results_dict["tenor"] = selected_tenor_main
                            results_dict["tax_rate"] = tax_rate_main
                            st.session_state.primary_results = results_dict
                        else:
                            st.error(prepare_arabic_text(results_dict["error"]))
                            st.session_state.primary_results = None
                    else:
                        st.session_state.primary_results = "error_no_data"
                else:
                    st.session_state.primary_results = None

    with col_results_main:
        if st.session_state.primary_results:
            if st.session_state.primary_results == "error_no_data":
                with st.container(border=True):
                    st.error(
                        prepare_arabic_text(
                            "لا توجد بيانات للعائد. يرجى تحديث البيانات أولاً."
                        )
                    )
            else:
                results = st.session_state.primary_results
                with st.container(border=True):
                    st.subheader(
                        prepare_arabic_text(
                            f"✨ ملخص استثمارك لأجل {results['tenor']} يوم"
                        ),
                        anchor=False,
                    )
                    st.markdown(
                        f"""<div style="text-align: center; margin-bottom: 20px;"><p style="font-size: 1.1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("النسبة الفعلية للربح (عن الفترة)")}</p><p style="font-size: 2.8rem; color: #ffc107; font-weight: 700; line-height: 1.2;">{results['real_profit_percentage']:.3f}%</p></div>""",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"""<div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; margin-bottom: 15px;"><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("💰 صافي الربح المقدم")} </p><p style="font-size: 1.9rem; color: #28a745; font-weight: 600; line-height: 1.2;">{format_currency(results['net_return'])}</p></div>""",
                        unsafe_allow_html=True,
                    )

                    # --- بداية التعديل المطلوب ---
                    # هذا الصندوق يعرض (القيمة الإسمية + الربح الصافي)
                    total_value = results["total_payout"] + results["net_return"]
                    st.markdown(
                        f"""<div style="text-align: center; background-color: #212529; padding: 10px; border-radius: 10px; "><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("المبلغ النهائي بعد الأرباح")}</p><p style="font-size: 1.9rem; color: #8ab4f8; font-weight: 600; line-height: 1.2;">{format_currency(total_value)}</p></div>""",
                        unsafe_allow_html=True,
                    )

                    st.divider()

                    with st.expander(
                        prepare_arabic_text("عرض تفاصيل الحساب الكاملة"), expanded=False
                    ):
                        st.markdown(
                            f"""<div style="padding: 10px; border-radius: 10px; background-color: #212529;">
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;"><span style="font-size: 1.1rem;">{prepare_arabic_text("سعر الشراء الفعلي (المبلغ المستثمر)")}</span><span style="font-size: 1.2rem; font-weight: 600;">{format_currency(results['purchase_price'])}</span></div>
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;"><span style="font-size: 1.1rem;">{prepare_arabic_text("العائد الإجمالي (قبل الضريبة)")}</span><span style="font-size: 1.2rem; font-weight: 600; color: #8ab4f8;">{format_currency(results['gross_return'])}</span></div>
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px;"><span style="font-size: 1.1rem;">{prepare_arabic_text(f"قيمة الضريبة المستحقة ({results['tax_rate']}%)")}</span><span style="font-size: 1.2rem; font-weight: 600; color: #dc3545;">{format_currency(results['tax_amount'])}</span></div>
                            </div>""",
                            unsafe_allow_html=True,
                        )

                        st.divider()

                    st.markdown(
                        "<div style='margin-top: 15px;'></div>", unsafe_allow_html=True
                    )
                    st.info(
                        prepare_arabic_text(
                            """**💡 آلية صرف العوائد والضريبة:**\n- **العائد الإجمالي (قبل الضريبة)** يُضاف إلى حسابك مقدمًا في يوم الشراء.\n- في نهاية المدة، تسترد **القيمة الإسمية الكاملة**.\n- **قيمة الضريبة** يتم خصمها من حسابك في تاريخ الاستحقاق. **لذا، يجب التأكد من وجود هذا المبلغ في حسابك لتجنب أي  خصم من المبلغ الأساسي.**"""
                        ),
                        icon="💡",
                    )
        else:
            with st.container(border=True):
                st.info(
                    "✨ ستظهر نتائج الحساب هنا بعد إدخال البيانات والضغط على زر الحساب.",
                    icon="💡",
                )

    st.divider()
    st.header(prepare_arabic_text(C.SECONDARY_CALCULATOR_TITLE))

    col_secondary_form, col_secondary_results = st.columns(2, gap="large")

    with col_secondary_form:
        with st.container(border=True):
            st.subheader(
                prepare_arabic_text("1. أدخل بيانات الإذن الأصلي"), anchor=False
            )
            face_value_secondary = st.number_input(
                prepare_arabic_text("القيمة الإسمية للإذن"),
                min_value=C.MIN_T_BILL_AMOUNT,
                value=C.MIN_T_BILL_AMOUNT,
                step=C.T_BILL_AMOUNT_STEP,
                key="secondary_face_value",
                help="القيمة الإسمية للإذن الذي اشتريته سابقاً.",
            )
            original_yield_secondary = st.number_input(
                prepare_arabic_text("عائد الشراء الأصلي (%)"),
                min_value=1.0,
                value=29.0,
                step=0.1,
                key="secondary_original_yield",
                format="%.3f",
                help="العائد الذي حصلت عليه عند شراء الإذن.",
            )
            original_tenor_secondary = st.selectbox(
                prepare_arabic_text("أجل الإذن الأصلي (بالأيام)"),
                options,
                key="secondary_tenor",
                help="مدة الإذن الأصلية.",
            )
            tax_rate_secondary = st.number_input(
                prepare_arabic_text("نسبة الضريبة على الأرباح (%)"),
                min_value=0.0,
                max_value=100.0,
                value=C.DEFAULT_TAX_RATE_PERCENT,
                step=0.5,
                format="%.1f",
                key="secondary_tax",
                help="نسبة الضريبة التي ستطبق على ربحك.",
            )

            st.subheader(prepare_arabic_text("2. أدخل تفاصيل البيع"), anchor=False)
            max_holding_days = (
                int(original_tenor_secondary) - 1 if original_tenor_secondary > 1 else 1
            )
            early_sale_days_secondary = st.number_input(
                prepare_arabic_text("أيام الاحتفاظ الفعلية (قبل البيع)"),
                min_value=1,
                value=min(60, max_holding_days),
                max_value=max_holding_days,
                step=1,
                help="عدد الأيام التي احتفظت بها بالإذن قبل أن تقرر بيعه.",
            )
            secondary_market_yield = st.number_input(
                prepare_arabic_text("العائد السائد في السوق للمشتري (%)"),
                min_value=1.0,
                value=30.0,
                step=0.1,
                format="%.3f",
                help="العائد الحالي في السوق الذي سيحصل عليه المشتري الجديد.",
            )

            if st.button(
                prepare_arabic_text("حلل سعر البيع الثانوي"),
                use_container_width=True,
                type="primary",
                key="secondary_calc",
            ):
                results = analyze_secondary_sale(
                    face_value_secondary,
                    original_yield_secondary,
                    original_tenor_secondary,
                    early_sale_days_secondary,
                    secondary_market_yield,
                    tax_rate_secondary,
                )
                if results.get("error"):
                    st.error(prepare_arabic_text(results["error"]))
                    st.session_state.secondary_results = None
                else:
                    st.session_state.secondary_results = results

    with col_secondary_results:
        if st.session_state.secondary_results:
            results = st.session_state.secondary_results
            with st.container(border=True):
                st.subheader(
                    prepare_arabic_text("✨ تحليل سعر البيع الثانوي"), anchor=False
                )
                if results["net_profit"] >= 0:
                    st.success(
                        f"البيع الآن يعتبر مربحًا. ستحقق ربحًا صافيًا قدره {format_currency(results['net_profit'])}.",
                        icon="✅",
                    )
                else:
                    st.warning(
                        f"البيع الآن سيحقق خسارة. ستبلغ خسارتك الصافية {format_currency(abs(results['net_profit']))}.",
                        icon="⚠️",
                    )

                st.divider()
                profit_color = "#28a745" if results["net_profit"] >= 0 else "#dc3545"
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"""<div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; height: 100%;"><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("🏷️ سعر البيع الفعلي")}</p><p style="font-size: 1.9rem; color: #8ab4f8; font-weight: 600; line-height: 1.2;">{format_currency(results['sale_price'])}</p></div>""",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.markdown(
                        f"""<div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; height: 100%;"><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("💰 صافي الربح / الخسارة")}</p><p style="font-size: 1.9rem; color: {profit_color}; font-weight: 600; line-height: 1.2;">{format_currency(results['net_profit'])}</p><p style="font-size: 1rem; color: {profit_color}; margin-top: -5px;">({results['period_yield']:.2f}% {prepare_arabic_text("عن فترة الاحتفاظ")})</p></div>""",
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    "<div style='margin-top: 15px;'></div>", unsafe_allow_html=True
                )
                with st.expander(prepare_arabic_text("عرض تفاصيل الحساب")):
                    st.markdown(
                        f"""<div style="padding: 10px; border-radius: 10px; background-color: #212529;"><div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;"><span style="font-size: 1.1rem;">{prepare_arabic_text("سعر الشراء الأصلي")}</span><span style="font-size: 1.2rem; font-weight: 600;">{format_currency(results['original_purchase_price'])}</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;"><span style="font-size: 1.1rem;">{prepare_arabic_text("إجمالي الربح (قبل الضريبة)")}</span><span style="font-size: 1.2rem; font-weight: 600; color: {'#28a745' if results['gross_profit'] >= 0 else '#dc3545'};">{format_currency(results['gross_profit'])}</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px;"><span style="font-size: 1.1rem;">{prepare_arabic_text(f"قيمة الضريبة ({tax_rate_secondary}%)")}</span><span style="font-size: 1.2rem; font-weight: 600; color: #dc3545;">-{format_currency(results['tax_amount'], currency_symbol='')}</span></div></div>""",
                        unsafe_allow_html=True,
                    )
                    st.divider()

                    if results["gross_profit"] <= 0:
                        st.info(
                            prepare_arabic_text(
                                "لا توجد ضريبة على الخسائر الرأسمالية."
                            ),
                            icon="ℹ️",
                        )

        else:
            with st.container(border=True):
                st.info("📊 ستظهر نتائج تحليل البيع هنا.", icon="💡")

    st.divider()
    st.header(prepare_arabic_text("📈 تطور العائد تاريخيًا"))

    if not historical_df.empty:
        available_tenors = sorted(historical_df[C.TENOR_COLUMN_NAME].unique())
        selected_tenors = st.multiselect(
            label=prepare_arabic_text("اختر الآجال التي تريد عرضها:"),
            options=available_tenors,
            default=available_tenors,
            label_visibility="collapsed",
        )
        if selected_tenors:
            chart_df = historical_df[
                historical_df[C.TENOR_COLUMN_NAME].isin(selected_tenors)
            ]
            fig = px.line(
                chart_df,
                x=C.DATE_COLUMN_NAME,
                y=C.YIELD_COLUMN_NAME,
                color=C.TENOR_COLUMN_NAME,
                markers=True,
                labels={
                    C.DATE_COLUMN_NAME: "تاريخ التحديث",
                    C.YIELD_COLUMN_NAME: "نسبة العائد (%)",
                    C.TENOR_COLUMN_NAME: "الأجل (يوم)",
                },
                title=prepare_arabic_text(
                    "التغير في متوسط العائد المرجح لأذون الخزانة"
                ),
            )
            fig.update_layout(
                legend_title_text=prepare_arabic_text("الأجل"),
                title_x=0.5,
                template="plotly_dark",
                xaxis=dict(tickformat="%d-%m-%Y"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                prepare_arabic_text(
                    "يرجى اختيار أجل واحد على الأقل لعرض الرسم البياني."
                )
            )
    else:
        st.info(
            prepare_arabic_text(
                "لا توجد بيانات تاريخية كافية لعرض الرسم البياني. قم بتحديث البيانات عدة مرات على مدار أيام مختلفة."
            )
        )

    st.divider()
    with st.expander(prepare_arabic_text(C.HELP_TITLE)):
        st.markdown(
            prepare_arabic_text(
                """
        #### **ما الفرق بين "العائد" و "الفائدة"؟**
        - **الفائدة (Interest):** تُحسب على أصل المبلغ وتُضاف إليه دورياً (مثل شهادات الادخار).
        - **العائد (Yield):** في أذون الخزانة، أنت تشتري الإذن بسعر **أقل** من قيمته الإسمية، وربحك هو الفارق الذي ستحصل عليه في نهاية المدة.
        ---
        #### **كيف تعمل حاسبة العائد الأساسية؟**
        1.  **حساب سعر الشراء:** `سعر الشراء = القيمة الإسمية ÷ (1 + (العائد ÷ 100) × (مدة الإذن ÷ 365))`
        2.  **حساب إجمالي الربح:** `إجمالي الربح = القيمة الإسمية - سعر الشراء`
        3.  **حساب الضريبة:** `إجمالي الربح × (نسبة الضريبة ÷ 100)`
        4.  **حساب صافي الربح:** `إجمالي الربح - قيمة الضريبة`
        ---
        #### **كيف تعمل حاسبة البيع في السوق الثانوي؟**
        هذه الحاسبة تجيب على سؤال: "كم سيكون ربحي أو خسارتي إذا بعت الإذن اليوم قبل تاريخ استحقاقه؟". سعر البيع هنا لا يعتمد على سعر شرائك، بل على سعر الفائدة **الحالي** في السوق.
        1.  **حساب سعر شرائك الأصلي:** بنفس طريقة الحاسبة الأساسية.
        2.  **حساب سعر البيع اليوم:** `الأيام المتبقية = الأجل الأصلي - أيام الاحتفاظ`، `سعر البيع = القيمة الإسمية ÷ (1 + (العائد السائد اليوم ÷ 100) × (الأيام المتبقية ÷ 365))`
        3.  **النتيجة النهائية:** `الربح أو الخسارة = سعر البيع - سعر الشراء الأصلي`. يتم حساب الضريبة على هذا الربح إذا كان موجباً.
        """
            )
        )
        st.markdown("---")
        st.subheader(prepare_arabic_text("تقدير رسوم أمين الحفظ"))
        st.markdown(
            prepare_arabic_text(
                """
        تحتفظ البنوك بأذون الخزانة الخاصة بك مقابل رسوم خدمة دورية. تُحسب هذه الرسوم كنسبة مئوية **سنوية** من **القيمة الإسمية** الإجمالية لأذونك، ولكنها تُخصم من حسابك بشكل **ربع سنوي** (كل 3 أشهر).

        تختلف هذه النسبة من بنك لآخر (عادة ما تكون حوالي 0.1% سنوياً). أدخل بياناتك أدناه لتقدير قيمة الخصم الربع سنوي المتوقع.
        """
            )
        )

        fee_col1, fee_col2 = st.columns(2)
        with fee_col1:
            total_face_value = st.number_input(
                prepare_arabic_text("إجمالي القيمة الإسمية لكل أذونك"),
                min_value=C.MIN_T_BILL_AMOUNT,
                value=100000.0,
                step=C.T_BILL_AMOUNT_STEP,
                key="fee_calc_total",
            )
        with fee_col2:
            fee_percentage = st.number_input(
                prepare_arabic_text("نسبة رسوم الحفظ السنوية (%)"),
                min_value=0.0,
                value=0.10,
                step=0.01,
                format="%.2f",
                key="fee_calc_perc",
            )

        annual_fee = total_face_value * (fee_percentage / 100.0)
        quarterly_deduction = annual_fee / 4

        st.markdown(
            f"""<div style='text-align: center; background-color: #212529; padding: 10px; border-radius: 10px; margin-top:10px;'><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("الخصم الربع سنوي التقريبي")}</p><p style="font-size: 1.5rem; color: #ffc107; font-weight: 600; line-height: 1.2;">{format_currency(quarterly_deduction)}</p></div>""",
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown(
            prepare_arabic_text(
                "\n\n***إخلاء مسؤولية:*** *هذا التطبيق هو أداة استرشادية فقط. للحصول على أرقام نهائية ودقيقة، يرجى الرجوع إلى البنك أو المؤسسة المالية التي تتعامل معها.*"
            )
        )


if __name__ == "__main__":
    main()
