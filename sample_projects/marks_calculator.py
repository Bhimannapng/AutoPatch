def calculate_grade(marks):
    """
    Calculates grade based on marks obtained (0 to 100).
    Bug: Missing validation for negative marks (<0) and values exceeding 100.
    """
    if marks >= 90:
        return "Grade A"
    elif marks >= 75:
        return "Grade B"
    elif marks >= 50:
        return "Grade C"
    elif marks >= 0:
        return "Fail"
    else:
        # Edge case bug: without validation, negative numbers or >100 return incorrect output
        return "Fail"

def main():
    # Normal inputs (Works)
    print("Marks 95 ->", calculate_grade(95))
    print("Marks 60 ->", calculate_grade(60))

    # Boundary & Invalid inputs (Fails business logic)
    print("Invalid Negative (-15) ->", calculate_grade(-15)) # Should raise ValueError or return 'Invalid Marks'
    print("Invalid Overflow (150) ->", calculate_grade(150)) # Returns Grade A instead of validating bounds

if __name__ == "__main__":
    main()
