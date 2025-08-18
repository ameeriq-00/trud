FROM python:3.11-slim

WORKDIR /app

# تثبيت التبعيات النظام
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات التبعيات
COPY requirements.txt .

# تثبيت التبعيات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إنشاء المجلدات المطلوبة
RUN mkdir -p data logs static/css static/js templates

# تعيين متغيرات البيئة
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

# فتح المنفذ
EXPOSE 8000

# تشغيل التطبيق
CMD ["python", "run.py"]