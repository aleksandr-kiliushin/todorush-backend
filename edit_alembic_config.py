import configparser


def edit_alembic_config():
    alembic_config_path = "./alembic.ini"

    with open(alembic_config_path, "r") as alembic_config:
        alembic_config_lines = alembic_config.readlines()

    # Load values from .env file
    env_config = configparser.ConfigParser()
    env_config.read("./.env")

    # Update sqlalchemy.url with the value from the .env file
    production_db_url = env_config.get("DEFAULT", "DB_URL", fallback=None)

    if production_db_url:
        for line_index, line in enumerate(alembic_config_lines):
            if line.startswith("sqlalchemy.url = "):
                alembic_config_lines[line_index] = f"sqlalchemy.url = {production_db_url}\n"
                break

        # Write the changes back to alembic.ini
        with open(alembic_config_path, "w") as file:
            file.writelines(alembic_config_lines)
        print("Updated alembic.ini with the secret DB_URL from env file")
    else:
        print("DB_URL not found in the env file")


if __name__ == "__main__":
    edit_alembic_config()
