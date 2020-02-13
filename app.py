import sys
import perora.spec
import perora.journal


def main() -> None:
    args = sys.argv[1:][0]
    if len(args) < 1:
        # TODO: List the available programs here
        print("Too few arguments")

    programs = {
        "j": perora.journal.launch_journal_editor,
        "s": perora.spec.spec,
        "e": perora.spec.review_reminder
    }

    selected_program = args[0]

    # Run program
    programs[selected_program]()


if __name__ == "__main__":
    main()
