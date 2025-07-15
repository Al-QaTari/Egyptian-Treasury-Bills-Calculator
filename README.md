<div align="center">
    <h1>🏦 حاسبة أذون الخزانة المصرية 🏦</h1>
  <p><strong>تطبيقك الأمثل لتحليل وحساب عوائد أذون الخزانة المصرية بدقة وسهولة.</strong></p>
  
  <p>
    <a href="https://egyptian-bills-calculator.streamlit.app/" target="_blank"><img src="https://img.shields.io/badge/Launch-App-FF4B4B?logo=streamlit" alt="Launch App"></a>
    <a href="https://github.com/Al-QaTari/Egyptian-Treasury-Bills-Calculator/actions/workflows/quality_check.yml"><img src="https://github.com/Al-QaTari/Egyptian-Treasury-Bills-Calculator/actions/workflows/quality_check.yml/badge.svg" alt="Code Quality Check"></a>
    <a href="https://github.com/Al-QaTari/Egyptian-Treasury-Bills-Calculator/actions/workflows/scheduled_scrape.yml"><img src="https://github.com/Al-QaTari/Egyptian-Treasury-Bills-Calculator/actions/workflows/scheduled_scrape.yml/badge.svg" alt="Scheduled Scrape"></a>
    <a href="https://streamlit.io" target="_blank"><img src="https://img.shields.io/badge/Made_with-Streamlit-FF4B4B?logo=streamlit" alt="Made with Streamlit"></a>
    <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python" alt="Python Version"></a>
  </p>
</div>

---

## 📖 جدول المحتويات
1. [عن المشروع](#-عن-المشروع)
2. [الميزات الرئيسية](#-الميزات-الرئيسية)
3. [التشغيل محلياً](#-التشغيل-محلياً)
4. [هيكل المشروع](#-هيكل-المشروع)
5. [الترخيص](#-الترخيص-license)
6. [المساهمة](#-المساهمة)
7. [المؤلف](#المؤلف)

---

## 🎯 عن المشروع

تطبيق ويب تفاعلي ومفتوح المصدر، تم بناؤه باستخدام **Streamlit** لمساعدة المستثمرين في السوق المصري على اتخاذ قرارات استثمارية مدروسة. يقوم التطبيق بسحب أحدث بيانات عطاءات أذون الخزانة بشكل آلي من موقع البنك المركزي المصري ويحولها إلى أرقام ورؤى واضحة.

---

## ✨ الميزات الرئيسية

| الميزة | الوصف |
| :--- | :--- |
| **📊 جلب آلي للبيانات** | سحب أحدث بيانات العطاءات مباشرة من موقع البنك المركزي المصري لضمان دقة الأرقام. |
| **🧮 حاسبة العائد الأساسية** | حساب صافي الربح، الضرائب، ونسبة العائد الفعلية عند الشراء والاحتفاظ حتى الاستحقاق. |
| **⚖️ حاسبة البيع الثانوي** | تحليل قرار البيع المبكر وحساب الربح أو الخسارة المحتملة بناءً على العائد السائد في السوق. |
| **🗄️ قاعدة بيانات تاريخية** | حفظ البيانات المجلوبة في قاعدة بيانات SQLite لتتبع التغيرات في العوائد مع مرور الوقت. |
| **⚙️ أتمتة كاملة (CI/CD)** | استخدام GitHub Actions لفحص جودة الكود، وتطبيق التنسيق، وتشغيل الاختبارات تلقائياً. |
| **💡 شرح مفصل** | قسم للمساعدة يشرح المفاهيم المالية الأساسية وكيفية عمل الحاسبات. |

---

## 🚀 التشغيل محلياً

اتبع هذه الخطوات لتشغيل المشروع على جهازك.

#### 1️⃣ المتطلبات الأساسية
- Python 3.8 أو أحدث.
- متصفح Google Chrome.
- أداة `git`.

#### 2️⃣ تثبيت المشروع
```bash
# انسخ المستودع إلى جهازك
git clone [https://github.com/Al-QaTari/Egyptian-Treasury-Bills-Calculator.git](https://github.com/Al-QaTari/Egyptian-Treasury-Bills-Calculator.git)

# ادخل إلى مجلد المشروع
cd Egyptian-Treasury-Bills-Calculator

# ثبّت جميع المكتبات المطلوبة
pip install -r requirements.txt
```

#### 3️⃣ تحديث البيانات (خطوة هامة)
```bash
# شغّل سكربت تحديث البيانات لجلب أحدث العوائد
python update_data.py
```
> **ملاحظة:** قد تستغرق هذه العملية دقيقة أو اثنتين في المرة الأولى.

#### 4️⃣ تشغيل التطبيق
```bash
# شغّل تطبيق Streamlit
streamlit run app.py
```
سيفتح التطبيق تلقائيًا في متصفحك على `http://localhost:8501`.

---

## 📂 هيكل المشروع
```
Egyptian-Treasury-Bills-Calculator/
│
├── .github/
│   └── workflows/
│       ├── quality_check.yml     # (CI): يفحص جودة الكود وتنسيقه مع كل تحديث.
│       ├── scheduled_scrape.yml  # (CI): يقوم بجدولة جلب البيانات بشكل دوري (يوميًا مثلاً).
│       └── virus-scan.yml        # (CI): يقوم بفحص الكود من الفيروسات كخطوة أمان إضافية.
│
├── css/
│   └── style.css                 # ملف التنسيقات (CSS) لتصميم الواجهة الرسومية.
│
├── tests/
│   ├── __init__.py               # ملف فارغ لجعل المجلد حزمة بايثون قابلة للاستيراد.
│   ├── test_calculations.py      # اختبارات للتأكد من صحة العمليات الحسابية.
│   ├── test_cbe_scraper.py       # اختبارات للتأكد من صحة تحليل بيانات الموقع.
│   ├── test_db_manager.py        # اختبارات للتأكد من أن حفظ وتحميل البيانات يعمل.
│   ├── test_integration.py       # اختبارات للتأكد من أن المكونات تعمل معًا بشكل سليم.
│   └── test_ui.py                # اختبارات لواجهة المستخدم باستخدام متصفح آلي.
│
├── app.py                        # الملف الرئيسي لواجهة المستخدم الرسومية (Streamlit).
├── calculations.py               # يحتوي على الدوال الخاصة بالعمليات الحسابية المالية.
├── cbe_scraper.py                # يحتوي على منطق جلب وتحليل البيانات من موقع البنك.
├── constants.py                  # لتخزين جميع القيم الثابتة (مثل العناوين والروابط).
├── db_manager.py                 # لإدارة كل عمليات قاعدة البيانات (إنشاء، حفظ، تحميل).
├── update_data.py                # سكربت لتشغيل عملية تحديث البيانات بشكل يدوي.
├── utils.py                      # يحتوي على دوال مساعدة مشتركة بين الملفات الأخرى.
│
├── .gitignore                    # لتحديد الملفات التي يجب على Git تجاهلها (مثل venv).
├── LICENSE.txt                   # ملف الترخيص الذي يحدد كيفية استخدام المشروع.
├── README.md                     # ملف التوثيق الرئيسي للمشروع (شرح، كيفية تثبيت).
├── packages.txt                  # قائمة بحزم نظام التشغيل المطلوبة للخوادم (مثل Streamlit Cloud).
└── requirements.txt              # قائمة بمكتبات بايثون المطلوبة لتشغيل المشروع.
```

---

## 📜 الترخيص (License)

هذا المشروع مرخص بموجب **ترخيص MIT**، وهو أحد أكثر تراخيص البرمجيات الحرة تساهلاً. هذا يمنحك حرية كبيرة في استخدام وتطوير البرنامج.

#### ✓ لك مطلق الحرية في:
- **الاستخدام التجاري**: يمكنك استخدام هذا البرنامج في أي مشروع تجاري وتحقيق الربح منه.
- **التعديل والتطوير**: يمكنك تعديل الكود المصدري ليناسب احتياجاتك الخاصة.
- **التوزيع**: يمكنك إعادة توزيع البرنامج بنسخته الأصلية أو بعد تعديله.

#### ⚠️ الشرط الوحيد:
- **الإبقاء على الإشعار**: يجب عليك الإبقاء على إشعار حقوق النشر والترخيص الأصلي مضمنًا في جميع نسخ البرنامج.

#### 🚫 إخلاء المسؤولية:
- **بدون ضمان**: البرنامج مقدم "كما هو" دون أي ضمان من أي نوع، سواء كان صريحًا أو ضمنيًا.
- **بدون مسؤولية**: لا يتحمل المؤلف أي مسؤولية عن أي أضرار قد تنشأ عن استخدام البرنامج.

<p align="center">
  <a href="https://github.com/Al-QaTari/Egyptian-Treasury-Bills-Calculator/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  </a>
  <br>
  <small>للاطلاع على النص الكامل للترخيص، اضغط على الشارة أعلاه</small>
</p>

---

## 🤝 المساهمة

المساهمات هي ما تجعل مجتمع المصادر المفتوحة مكانًا رائعًا للتعلم والإلهام والإبداع. أي مساهمات تقدمها ستكون موضع **تقدير كبير**.

1.  قم بعمل Fork للمشروع.
2.  أنشئ فرعًا جديدًا للميزة الخاصة بك (`git checkout -b feature/AmazingFeature`).
3.  قم بعمل Commit لتغييراتك (`git commit -m 'Add some AmazingFeature'`).
4.  ارفع تغييراتك إلى الفرع (`git push origin feature/AmazingFeature`).
5.  افتح Pull Request.

---

<h2 align="center">المؤلف</h2>
<p align="center"><strong>Mohamed AL-QaTri</strong> - <a href="https://github.com/Al-QaTari">GitHub</a></p>


---

<h3 align="center">⚠️ إخلاء مسؤولية</h3>
<p align="center">
هذا التطبيق هو أداة إرشادية فقط. للحصول على أرقام نهائية ودقيقة، يرجى الرجوع دائمًا إلى البنك أو المؤسسة المالية التي تتعامل معها.
</p>

