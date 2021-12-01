def clear_screen():
    print("\033[H\033[J")


def get_on_question_required(selector):
    def print_streak_message(streak):
        if streak == 30:
            print("That's 30 questions answered correctly in a row! Congratulations!\n---\n")
        elif streak == 20:
            print("That's 20 questions answered correctly in a row! Good job!\n---\n")
        elif streak == 10:
            print("That's 10 questions answered correctly in a row! Keep on going!\n---\n")

    def on_question_required(state, context):
        clear_screen()
        print_streak_message(context.get("right_answers_streak", 0))
        question, tag = selector.load_next_question()
        print(tag, "/", question, end="")
        return state.QUESTION_DISPLAYED

    return on_question_required