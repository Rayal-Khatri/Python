total_minutes = 0
total_models = 0

print("=== 3D Model Per Hour Calculator ===")
print("Type 'quit' to exit\n")

while True:
    model_num = total_models + 1
    user_input = input(f"Enter time for model {model_num} (mins): ").strip()

    if user_input.lower() == 'quit':
        print("\n=== Final Summary ===")
        if total_models > 0:
            final_mph = (total_models / total_minutes) * 60
            print(f"Total Models  : {total_models}")
            print(f"Total Time    : {total_minutes} mins ({total_minutes / 60:.2f} hrs)")
            print(f"Final MPH     : {final_mph:.2f}")
        else:
            print("No models recorded.")
        break

    try:
        minutes = float(user_input)
        if minutes == 0:
            print("0 mins entered, defaulting to 0.1 mins.")
            minutes = 0.1
        elif minutes < 0:
            print("Please enter a positive number.\n")
            continue

        total_models += 1
        total_minutes += minutes
        mph = (total_models / total_minutes) * 60

        print(f"MPH           : {mph:.2f}\n")

    except ValueError:
        print("Invalid input. Please enter a number or 'quit'.\n")