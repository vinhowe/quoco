import sys
import perora.spec
import perora.plan
import perora.manager


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 1:
        # TODO: List the available programs here
        print("Too few arguments")

    programs = {
        "s": perora.spec.spec,
        "e": perora.spec.review_reminder,
        "p": perora.plan.whats_the_plan,
        "m": perora.manager.edit_catalog
    }

    selected_program = args[0][0]
    program_arguments = " ".join(args[1:]) if len(args) > 1 else None

    # Run program
    if program_arguments is not None:
        programs[selected_program](program_arguments)
    else:
        programs[selected_program]()


if __name__ == "__main__":
    main()
