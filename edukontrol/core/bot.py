import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import asyncio
import os
import django
import sys
from asgiref.sync import sync_to_async

from aiogram import Router, F
router = Router()

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edukontrol.settings')
django.setup()

from core.models import School, Student, Test, Score, Rating
from django.contrib.auth.models import User

# Test topshirish uchun FSM
class TestStates(StatesGroup):
    waiting_answer = State()

@router.message(F.text == '/test')
async def start_test(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username or f'user_{telegram_id}'
    try:
        user = await sync_to_async(User.objects.get)(username=username)
        student = await sync_to_async(Student.objects.get)(user=user)
    except Exception as e:
        logger.warning(f"/test: User not registered: {username} ({telegram_id}) - {e}")
        await message.answer("Avval ro'yxatdan o'ting!")
        return

    # Shu sinf uchun birinchi testni olish
    try:
        test = await sync_to_async(lambda: Test.objects.filter(grade=student.grade).order_by('id').first())()
    except Exception as e:
        logger.error(f"/test: Error fetching test for {username} ({telegram_id}): {e}")
        await message.answer("Testlarni olishda xatolik yuz berdi.")
        return
    if not test:
        logger.info(f"/test: No test found for grade {student.grade} - {username} ({telegram_id})")
        await message.answer("Siz uchun testlar mavjud emas yoki testlar hali tuzilmadi.")
        return

    # Savollar va javoblarni olish
    from core.models import Question, Answer
    try:
        questions = await sync_to_async(lambda: list(Question.objects.filter(test=test)))()
    except Exception as e:
        logger.error(f"/test: Error fetching questions for test {test.id} - {username} ({telegram_id}): {e}")
        await message.answer("Test savollarini olishda xatolik yuz berdi.")
        return
    if not questions:
        logger.info(f"/test: No questions for test {test.id} - {username} ({telegram_id})")
        await message.answer("Testda savollar mavjud emas yoki testlar hali tuzilmadi.")
        return

    await state.update_data(
        test_id=test.id,
        questions=[q.id for q in questions],
        answers=[],
        current=0
    )
    logger.info(f"/test: Test started for {username} ({telegram_id}), test_id={test.id}")
    await message.answer(f"1-savol:\n{questions[0].text}")
    await state.set_state(TestStates.waiting_answer)

@router.message(TestStates.waiting_answer)
async def process_test_answer(message: types.Message, state: FSMContext):
    from core.models import Question, Answer
    data = await state.get_data()
    answers = data.get('answers', [])
    questions = data.get('questions', [])
    current = data.get('current', 0)

    # Foydalanuvchi javobini saqlash
    answers.append(message.text)
    current += 1

    if current < len(questions):
        # Keyingi savolni yuborish
        next_question_id = questions[current]
        try:
            next_question = await sync_to_async(Question.objects.get)(id=next_question_id)
        except Exception as e:
            logger.error(f"Test answer: Error fetching next question id={next_question_id}: {e}")
            await message.answer("Keyingi savolni olishda xatolik yuz berdi.")
            await state.clear()
            return
        await state.update_data(answers=answers, current=current)
        await message.answer(f"{current+1}-savol:\n{next_question.text}")
    else:
        # Test tugadi, natijani hisoblash
        test_id = data.get('test_id')
        try:
            test = await sync_to_async(Test.objects.get)(id=test_id)
        except Exception as e:
            logger.error(f"Test answer: Error fetching test id={test_id}: {e}")
            await message.answer("Test ma'lumotlarini olishda xatolik yuz berdi.")
            await state.clear()
            return
        correct = 0
        for idx, qid in enumerate(questions):
            try:
                question = await sync_to_async(Question.objects.get)(id=qid)
                # To‘g‘ri javobni olish
                correct_answer = await sync_to_async(lambda: Answer.objects.filter(question=question, is_correct=True).first())()
                if correct_answer and answers[idx].strip().lower() == correct_answer.text.strip().lower():
                    correct += 1
            except Exception as e:
                logger.error(f"Test answer: Error checking answer for question id={qid}: {e}")

        # Ballarni hisoblash va saqlash
        telegram_id = message.from_user.id
        username = message.from_user.username or f'user_{telegram_id}'
        try:
            user = await sync_to_async(User.objects.get)(username=username)
            student = await sync_to_async(Student.objects.get)(user=user)
            raw_score = correct
            weighted_score = correct  # Agar og‘irlik bo‘lsa, shu yerda hisoblang
            await sync_to_async(Score.objects.update_or_create)(
                student=student, test=test,
                defaults={'raw_score': raw_score, 'weighted_score': weighted_score}
            )
            logger.info(f"Test finished: {username} ({telegram_id}) test_id={test_id} correct={correct}/{len(questions)}")
        except Exception as e:
            logger.error(f"Test answer: Error saving score for {username} ({telegram_id}) test_id={test_id}: {e}")
            await message.answer("Natijani saqlashda xatolik yuz berdi.")
            await state.clear()
            return
        await message.answer(f"Test yakunlandi!\nTo‘g‘ri javoblar soni: {correct} / {len(questions)}")
        await state.clear()

API_TOKEN = '7775904021:AAHrPeOXkigRPa0Wn3IvMXAtDPZpH0n0-mE'

log_file = '/tmp/bot.log'
logger = logging.getLogger('bot_logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(file_handler)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

dp['bot'] = bot



# Stepik ro'yxatdan o'tish uchun FSM
from aiogram import Router, F
router = Router()

class RegisterStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_region = State()
    waiting_district = State()
    waiting_school = State()
    waiting_grade = State()

regions = [
    "Toshkent shahri", "Toshkent viloyati", "Andijon viloyati", "Farg'ona viloyati", "Namangan viloyati",
    "Samarqand viloyati", "Buxoro viloyati", "Navoiy viloyati", "Qashqadaryo viloyati", "Surxondaryo viloyati",
    "Jizzax viloyati", "Sirdaryo viloyati", "Xorazm viloyati", "Qoraqalpog'iston Respublikasi"
]

districts = {
    "Toshkent shahri": ["Yunusobod", "Chilonzor", "Yakkasaroy", "Olmazor", "Shayxontohur", "Uchtepa", "Yashnobod", "Mirobod", "Sergeli", "Bektemir", "Mirzo Ulug'bek", "Yangihayot"],
    "Samarqand viloyati": ["Samarqand shahri", "Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on", "Narpay", "Nurobod", "Oqdaryo", "Paxtachi", "Payariq", "Pastdarg'om", "Qo'shrabot", "Samarqand", "Tayloq", "Urgut"],
    # ... boshqa viloyatlar uchun ham to'ldirish mumkin
}




# /start - ro'yxatdan o'tish yoki login
@router.message(F.text.startswith('/start'))
async def send_welcome(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username or f'user_{telegram_id}'
    user_exists = await sync_to_async(User.objects.filter(username=username).exists)()
    if user_exists:
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz!\nBotdan foydalanishni davom ettirishingiz mumkin.\nAgar login qilishni istasangiz, /login buyrug'ini yuboring.")
        await state.clear()
        return
    await message.answer("Assalomu alaykum! Ta'lim reyting botiga xush kelibsiz!\nRo'yxatdan o'tish uchun ism va familiyangizni kiriting:")
    await state.set_state(RegisterStates.waiting_name)

# /login - faqat ro'yxatdan o'tganlar uchun login qilish
@router.message(F.text.startswith('/login'))
async def login_user(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username or f'user_{telegram_id}'
    user_exists = await sync_to_async(User.objects.filter(username=username).exists)()
    if user_exists:
        await message.answer("Siz tizimga muvaffaqiyatli kirdingiz! Botdan foydalanishingiz mumkin.")
        await state.clear()
    else:
        await message.answer("Siz ro'yxatdan o'tmagansiz. Avval /start orqali ro'yxatdan o'ting.")
        await state.clear()

@router.message(RegisterStates.waiting_name)
async def process_name(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username or f'user_{telegram_id}'
    # Agar user allaqachon mavjud bo'lsa, ro'yxatdan o'tkazmaymiz
    user_exists = await sync_to_async(User.objects.filter(username=username).exists)()
    if user_exists:
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz! Botdan foydalanishni davom ettirishingiz mumkin.")
        await state.clear()
        return
    await state.update_data(full_name=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=kb)
    await state.set_state(RegisterStates.waiting_phone)

@router.message(RegisterStates.waiting_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=reg)] for reg in regions],
        resize_keyboard=True
    )
    await message.answer("Viloyatingizni tanlang:", reply_markup=kb)
    await state.set_state(RegisterStates.waiting_region)

@router.message(RegisterStates.waiting_region)
async def process_region(message: types.Message, state: FSMContext):
    region = message.text
    await state.update_data(region=region)
    # Shaharlar uchun tuman so'ralmaydi
    if region.endswith("shahri"):
        await state.update_data(district=region)
        await message.answer("Maktab raqamini kiriting:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(RegisterStates.waiting_school)
    else:
        vil_districts = districts.get(region, [])
        if vil_districts:
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=d)] for d in vil_districts],
                resize_keyboard=True
            )
            await message.answer("Tumanni tanlang:", reply_markup=kb)
        else:
            await message.answer("Tumanni matn ko'rinishida kiriting:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(RegisterStates.waiting_district)

@router.message(RegisterStates.waiting_district)
async def process_district(message: types.Message, state: FSMContext):
    await state.update_data(district=message.text)
    await message.answer("Maktab raqamini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.waiting_school)

@router.message(RegisterStates.waiting_school)
async def process_school(message: types.Message, state: FSMContext):
    await state.update_data(school_number=message.text)
    await message.answer("Nechanchi sinfda o'qiysiz? (raqam bilan kiriting)")
    await state.set_state(RegisterStates.waiting_grade)

@router.message(RegisterStates.waiting_grade)
async def process_grade(message: types.Message, state: FSMContext):
    data = await state.get_data()
    grade = int(message.text)
    telegram_id = message.from_user.id
    username = message.from_user.username or f'user_{telegram_id}'
    # User va School yaratish yoki olish
    user, _ = await sync_to_async(User.objects.get_or_create)(username=username, defaults={
        'first_name': data.get('full_name', '').split()[0] if data.get('full_name') else '',
        'last_name': ' '.join(data.get('full_name', '').split()[1:]) if data.get('full_name') else ''
    })
    school, _ = await sync_to_async(School.objects.get_or_create)(
        name=data.get('school_number'),
        region=data.get('region'),
        district=data.get('district')
    )
    await sync_to_async(Student.objects.update_or_create)(
        user=user,
        defaults={
            'school': school,
            'grade': grade,
            'phone': data.get('phone')
        }
    )
    await message.answer("Ro'yxatdan o'tish yakunlandi! Endi botdan foydalanishingiz mumkin.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@router.message(F.text.startswith('/register'))
async def register_user(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or f'user_{telegram_id}'
    first_name = message.from_user.first_name or ''
    last_name = message.from_user.last_name or ''
    if await sync_to_async(User.objects.filter(username=username).exists)():
        await message.reply("Siz allaqachon ro'yxatdan o'tgansiz!")
        return
    user = await sync_to_async(User.objects.create)(username=username, first_name=first_name, last_name=last_name)
    await message.reply("Ro'yxatdan o'tdingiz! Endi maktab va sinf ma'lumotlaringizni yuboring: \n/myschool <maktab nomi> <sinf raqami>")

@router.message(F.text.startswith('/myschool'))
async def set_school_grade(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or f'user_{telegram_id}'
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.reply("Iltimos, maktab nomi va sinf raqamini kiriting: /myschool <maktab nomi> <sinf raqami>")
        return
    school_name = args[0]
    grade = int(args[1])
    user = await sync_to_async(User.objects.get)(username=username)
    school, _ = await sync_to_async(School.objects.get_or_create)(name=school_name, defaults={'region': '', 'district': ''})
    await sync_to_async(Student.objects.update_or_create)(user=user, defaults={'school': school, 'grade': grade})
    await message.reply(f"Maktab va sinf ma'lumotlari saqlandi: {school_name}, {grade}-sinf.")

@router.message(F.text.startswith('/myrating'))
async def my_rating(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or f'user_{telegram_id}'
    try:
        user = await sync_to_async(User.objects.get)(username=username)
        student = await sync_to_async(Student.objects.get)(user=user)
        rating = await sync_to_async(lambda: Rating.objects.filter(student=student).order_by('-total_score').first())()
        if rating:
            await message.reply(f"Sizning umumiy reytingingiz: {rating.total_score}")
        else:
            await message.reply("Sizda reyting ma'lumotlari topilmadi.")
    except Exception:
        await message.reply("Siz ro'yxatdan o'tmagansiz yoki ma'lumotlar topilmadi.")

if __name__ == '__main__':
    async def main():
        dp.include_router(router)
        await dp.start_polling(bot)

    asyncio.run(main())
