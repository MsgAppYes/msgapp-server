# msgapp-server
This is the code for the msgapp server/gateway.

# How to setup:
1. Install python and pip from [here](https://python.org)
2. Then install pipenv using pip with `pip install pipenv`
2. Then, install all the dependencies with `pipenv sync` in the project directory

# How to run:
1. Set it up by following the above
2. Add users with `pipenv run python create_user.py users.db <username>`
3. Customise the message of the day (motd) shown to the users when joining by editing `modt.txt`
4. Run the code using `pipenv run python main.py`
5. You can remove users with `pipenv run python revoke_user.py users.db <username>`
