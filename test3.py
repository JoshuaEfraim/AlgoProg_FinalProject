import speech_recognition as sr
from gtts import gTTS
import winsound
from pydub import AudioSegment
from expense import Expense
import datetime
import calendar
import os

def listen_for_command():
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("listening for commands...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        
    try: 
        command = recognizer.recognize_google(audio)
        print("you said:", command)
        return command.lower()
    except sr.UnknownValueError:
        print("Could not understand audio. Please try again.")
        return None
    except sr.RequestError:
        print("Unable to access Google Speech Recognition API")
        return None

def respond(response_text):
    print(response_text)
    tts = gTTS(text=response_text, lang='en')
    tts.save("response.mp3")
    sound = AudioSegment.from_mp3("response.mp3")
    sound.export("response.wav", format="wav")
    winsound.PlaySound("response.wav", winsound.SND_FILENAME)

def format_number_and_words(number):
    formatted_number = "{:,}".format(number)  # Format the number with commas for readability
    return formatted_number




BUDGET_FILE_PATH = "budget.txt"



def get_or_set_user_budget(change=False):
    if not change and os.path.exists(BUDGET_FILE_PATH):
        with open(BUDGET_FILE_PATH, "r") as budget_file:
            try:
                budget = int(budget_file.read())
                formatted_budget = format_number_and_words(budget)
                respond(f"Your current budget is {formatted_budget}")
                return budget
            except ValueError:
                respond("Error reading budget file. Setting a new budget.")
    return set_user_budget()


def set_user_budget():
    budget = None

    while budget is None:
        respond("Please set your budget for this month.")
        budget_text = listen_for_command()

        try:
            words = budget_text.lower().split()
            numeric_value = 0
            current_number = 0

            for word in words:
                word = word.replace(',', '').replace('.', '')
                if word.isdigit():
                    current_number = int(word)
                elif word == 'and':
                    continue  # Skip 'and' in combined phrases
                elif word == 'million':
                    numeric_value += current_number * 1000000
                    current_number = 0
                elif word == 'thousand':
                    numeric_value += current_number * 1000
                    current_number = 0

            # Handle any remaining number after the last 'million' or 'thousand'
            numeric_value += current_number

            budget = numeric_value
            
            formatted_budget = format_number_and_words(budget)
            respond(f"You've set your budget to {formatted_budget}")
            
            with open(BUDGET_FILE_PATH, "w") as budget_file:
                budget_file.write(str(budget))
        except ValueError:
            respond("Invalid input. Please provide a valid number for the budget.")

    return budget




def main():
    expense_file_path = "expenses.csv"
    budget = get_or_set_user_budget()  # Get the user's budget
    
    while True:
        respond("What would you like to do")
        usercommand = listen_for_command()
        
        if usercommand == "input my expense":
            expense = get_user_expense()
            save_expense_to_file(expense, expense_file_path)
        elif usercommand == "read and summarize my expenses":
            summarize_expenses(expense_file_path, budget)
        elif usercommand == "change my budget":
            budget = get_or_set_user_budget(change=True)  # Change the user's budget
        elif usercommand == "exit":
            respond("Exiting the program.")
            break
        else:
            respond("I'm sorry, I didn't understand that command. Please try again.")


def get_user_expense():
    expense_name = None
    expense_amount = None
    selected_category = None
    respond("Getting details for expenses")
    
    while expense_name is None:
        respond("please say the expense name")
        expense_name = listen_for_command()
        
    while expense_amount is None:
        respond("please say the expense amount")
        amount_text = listen_for_command()
        try:
            expense_amount = int(amount_text)
            formatted_expense_amount = format_number_and_words(expense_amount)
            print(f"You've entered {formatted_expense_amount}")
        except ValueError:
            respond("Invalid input. Please provide a valid number for the expense amount.")
    
    expense_categories = ["food", "home", "work", "fun", "others"]
    
    while selected_category is None:
        respond("please select a category for your expense: ")
        category_command = listen_for_command().lower()
        print(f"you said {category_command}")
        
        if category_command in expense_categories:
            selected_category = category_command
            new_expense = Expense(name=expense_name, category=selected_category, amount=expense_amount)
            respond(f"Expense details captured. {new_expense}")
            return new_expense
        else:
            respond("Invalid category, please try again.")

def save_expense_to_file(expense, expense_file_path):
    print(f"saving user expense: {expense} to {expense_file_path}")
    with open(expense_file_path, "a") as f:
        f.write(f"{expense.name}, {expense.category}, {expense.amount}\n")

def summarize_expenses(expense_file_path, budget):
    print("summarizing user expenses")
    expenses = []
    
    with open(expense_file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            stripped_line = line.strip()
            expense_name, expense_category, expense_amount = stripped_line.split(",")
            line_expense = Expense(name=expense_name, category=expense_category, amount=int(expense_amount))
            expenses.append(line_expense)
    
    amount_by_category = {}
    for expense in expenses:
        key = expense.category
        if key in amount_by_category:
            amount_by_category[key] += expense.amount
        else:
            amount_by_category[key] = expense.amount
    
    respond("Expenses by category:")
    
    for key, amount in amount_by_category.items():
        formatted_amount = format_number_and_words(amount)
        respond(f"  {key}: {formatted_amount}")
    
    total_spent = sum([ex.amount for ex in expenses])
    formatted_total_spent = format_number_and_words(total_spent)
    respond(f"you have spent {formatted_total_spent} this month!")
    
    remaining_budget = budget - total_spent
    formatted_remaining_budget= format_number_and_words(remaining_budget)
    respond(f"your remaining budget is {formatted_remaining_budget}")
    
    now = datetime.datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    remaining_days = days_in_month - now.day
    respond(f"remaining days in the current month: {remaining_days}")
    
    daily_budget = remaining_budget // remaining_days
    formatted_daily_budget = format_number_and_words(daily_budget)
    respond(f"your budget per day: {formatted_daily_budget}")

if __name__ == "__main__":
    main()