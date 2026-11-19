def calculate_grade(marks):
    # Bug: Missing validation for negative marks (<0) and values exceeding 100
    if marks >= 90:
        return "Grade A"
    elif marks >= 75:
        return "Grade B"
    elif marks >= 50:
        return "Grade C"
    elif marks >= 0:
        return "Fail"
    else:
        return "Fail"  # Negative marks return 'Fail' instead of input validation error

def main():
    print("Normal mark 85:", calculate_grade(85))
    print("Invalid negative mark -15:", calculate_grade(-15))
    print("Invalid overflow mark 150:", calculate_grade(150))

if __name__ == "__main__":
    main()