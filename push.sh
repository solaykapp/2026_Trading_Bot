#!/bin/bash
echo "🚀 جاري تشغيل الثلاثية السريعة للرفع..."
git add .
read -p "📝 ما هو وصف هذا التعديل؟: " msg
git commit -m "$msg"
git push
echo "✅ تم الحفظ والرفع بنجاح يا أسامة!"

