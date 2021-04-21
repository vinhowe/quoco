import sys
import quoco.spec
import quoco.plan
import quoco.quocofs_migration


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 1:
        # TODO: List the available programs here
        print("Too few arguments")

    programs = {
        "s": quoco.spec.spec,
        "e": quoco.spec.review_reminder,
        "p": quoco.plan.whats_the_plan,
        "m": quoco.quocofs_migration.edit_catalog,
        "d": quoco.quocofs_migration.download_documents,
        "G": quoco.quocofs_migration.migrate,
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
