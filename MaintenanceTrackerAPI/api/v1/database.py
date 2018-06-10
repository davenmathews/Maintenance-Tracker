import os

import psycopg2


class Database:
    def __init__(self,
                 db: str = os.getenv('DB_NAME'),
                 user: str = os.getenv('DB_USER'),
                 password: str = os.getenv('DB_PASSWORD')):

        if os.getenv('APP_CONFIG_NAME') == 'production':
            DATABASE_URL = os.environ['DATABASE_URL']
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            self.conn = psycopg2.connect(database=db,
                                         user=user,
                                         password=password)

        self.cur = None

    def query(self, query: str):
        """
        Method to perform most queries
        :param query: The sql query
        :return: None
        """
        self.cur = self.conn.cursor()
        try:
            self.cur.execute(query)
        except Exception as e:
            self.cur.connection.rollback()
            return e.args[0]

    def close(self):
        """
        Method to close cursor and connection
        :return: None
        """
        self.cur.close()
        self.conn.close()

    def create_all(self):
        """
        Method to create all tables that will be used in the database
        :return: None
        """
        create_users_table = "CREATE TABLE if not exists users (" \
                             "id serial PRIMARY KEY," \
                             "email varchar UNIQUE NOT NULL," \
                             "password_hash varchar NOT NULL," \
                             "security_question varchar NOT NULL," \
                             "security_answer_hash varchar NOT NULL," \
                             "role varchar NOT NULL DEFAULT 'Consumer');"
        self.query(create_users_table)
        self.conn.commit()

        create_requests_table = "CREATE TABLE if not exists requests (" \
                                "id serial PRIMARY KEY," \
                                "user_id integer references" \
                                " users(id) NOT NULL," \
                                "type varchar NOT NULL DEFAULT 'Repair'," \
                                "title varchar NOT NULL," \
                                "description varchar NOT NULL," \
                                "status varchar NOT NULL" \
                                " DEFAULT 'Pending Approval'," \
                                "date_requested timestamp NOT NULL," \
                                "last_modified timestamp," \
                                "requested_by varchar not null);"
        self.query(create_requests_table)
        self.conn.commit()

        create_token_blacklist_table = "CREATE TABLE if not exists tokens (" \
                                       "id serial PRIMARY KEY," \
                                       "jti varchar NOT NULL unique," \
                                       "expires timestamp NOT NULL);"
        self.query(create_token_blacklist_table)
        self.conn.commit()

    def drop_all(self):
        """
        Method to delete all tables from the database that are used by the app
        :return: None
        """
        self.query("drop table if exists requests;")
        self.query("drop table if exists users;")
        self.query("drop table if exists tokens;")
        self.conn.commit()

    def get_all_users(self):
        """
        Method to retrieve all users from the database.
        :return: a list of dictionaries containing users information
        :rtype list
        """
        query = 'select * from users;'
        self.query(query)
        items = self.cur.fetchall()
        if not items:
            return []
        users_list = []
        for user in items:
            user_dict = dict(
                user_id=user[0],
                email=user[1],
                role=user[-1]
            )
            users_list.append(user_dict)
        self.conn.commit()
        return users_list

    def get_user_by_id(self, user_id: int):
        """
        Method to get a user by the given id
        :param user_id: the id to search with
        :return: A dictionary containing user's information
        :rtype dict
        """
        query = "select * from users where id={}".format(user_id)
        self.query(query)
        items = self.cur.fetchall()
        if not items:
            return None
        else:
            item = items[0]
            user = dict(
                user_id=item[0],
                email=item[1],
                role=item[5]
            )
        self.conn.commit()
        return user

    def get_user_by_email(self, email: str):
        """
        Returns a dictionary with the user details if a user is found.
        Returns None otherwise
        :param email: the email to search with
        :rtype: dict
        """
        query = "select * from users where email={}".format("'" + email + "'")
        self.query(query)
        try:
            item = self.cur.fetchone()
        except Exception:
            return None

        if not item:
            user = None
        else:
            user = dict(
                user_id=item[0],
                email=item[1],
                password_hash=item[2],
                security_question=item[3],
                security_answer_hash=item[4],
                role=item[5]
            )
        self.conn.commit()
        return user

    def save_user(self, user):
        """
        Method that saves a user into the database
        :param user: The User Object
        :return: None
        """
        email = user.email
        password_hash = user.password_hash
        security_question = user.security_question
        security_answer_hash = user.security_answer_hash
        role = user.role
        sql = 'insert into users(email, password_hash, security_question,' \
              ' security_answer_hash, role) values(%s, %s, %s, %s, %s)'
        data = (email, password_hash, security_question, security_answer_hash
                , role)
        self.cur = self.conn.cursor()
        self.cur.execute(sql, data)
        self.conn.commit()

    def save_request(self, request):
        """
        Method that saves a request into the database
        :param request: The Request object
        :return: None
        """
        user_id = request.user_id
        request_type = request.type
        title = request.title
        description = request.description
        date_requested = request.date_requested
        requested_by = request.requested_by
        sql = 'insert into requests(user_id, type, title, description,' \
              ' date_requested, requested_by) values' \
              '(%s, %s, %s, %s, %s, %s)'
        data = (user_id, request_type, title, description, date_requested,
                requested_by)
        self.cur = self.conn.cursor()
        self.cur.execute(sql, data)
        self.conn.commit()

    def get_token_by_jti(self, jti):
        """
        Method that retrieves blacklisted tokens from the database
        :param jti: the Json Token Identifier
        :return: True if the token is found, False otherwise
        :rtype bool
        """
        query = "select * from tokens where jti={}".format(
            "'" + jti + "'")
        self.query(query)
        tokens = self.cur.fetchall()
        self.conn.commit()
        if tokens:
            return tokens[0]
        else:
            return None

    def get_requests(self):
        """
        Method for retrieving all requests from the database
        :return: A list of dictionaries containing request information
        :rtype list
        """
        query = 'select * from requests;'
        self.query(query)
        requests = self.cur.fetchall()
        if not requests:
            return []
        return_list = []
        for a_request in requests:
            request_dict = dict(
                request_id=a_request[0],
                requested_by=a_request[8],
                request_type=a_request[2],
                title=a_request[3],
                description=a_request[4],
                date_requested=str(a_request[6]),
                status=a_request[5],
                last_modified=str(a_request[7])
            )
            return_list.append(request_dict)
        self.conn.commit()
        return return_list

    def get_my_requests(self, user_id: int):
        """
        Method for retrieving all requests belonging to a user with the given
        user id
        :param user_id:
        :return: A list of dictionaries containing request information
        :rtype list
        """
        sql = 'select * from requests where user_id=%s;'
        data = (user_id,)
        self.cur = self.conn.cursor()
        self.cur.execute(sql, data)
        requests = self.cur.fetchall()
        if not requests:
            return []
        return_list = []
        for a_request in requests:
            request_dict = dict(
                request_id=a_request[0],
                requested_by=a_request[8],
                request_type=a_request[2],
                title=a_request[3],
                description=a_request[4],
                date_requested=str(a_request[6]),
                status=a_request[5],
                last_modified=str(a_request[7])
            )
            return_list.append(request_dict)
        self.conn.commit()
        return return_list

    def get_request_by_id(self, request_id: int):
        """
        Method for retrieving a request of the given id
        :param request_id:
        :return A list of dictionaries containing request information
        :rtype list
        """
        sql = 'select * from requests where id=%s;'
        data = (request_id,)
        self.cur = self.conn.cursor()
        self.cur.execute(sql, data)
        requests = self.cur.fetchall()
        if not requests:
            return []
        a_request = requests[0]
        request_dict = dict(
            request_id=a_request[0],
            requested_by=a_request[8],
            request_type=a_request[2],
            title=a_request[3],
            description=a_request[4],
            date_requested=str(a_request[6]),
            status=a_request[5],
            last_modified=str(a_request[7])
        )
        self.conn.commit()
        return request_dict

    def update_request(self, new_request: dict, old_request: dict):
        """
        Method to update requests
        Takes in  dictionaries and looks for changes in them
        If there are changes, the attribute name which corresponds to a column
        in the database, and the changed value are added into the 'change_list'
        as tuples
        Each column, value pair is updated one by one
        :param new_request:
        :param old_request:
        :return: None
        """
        # add things to be updated in a list of tuples
        change_list = []
        self.cur = self.conn.cursor()
        for key, value in new_request.items():
            if old_request.get(key) != value:
                change_list.append((key, value))
        # query the database to persist changes
        for column, value in change_list:
            sql = "update requests set {}=%s where id=%s;".format(column)
            data = (value, new_request['request_id'])
            self.cur.execute(sql, data)
        self.conn.commit()

    def change_role(self, action: str, user_id: int):
        """
        Method used to change the role of a user
        :param action: promote or demote
        :param user_id:
        :return: The changed user dictionary
        """
        sql = "update users set role=%s where id=%s;"
        data = None
        if action == 'promote':
            data = ('Administrator', user_id)
        elif action == 'demote':
            data = ('Consumer', user_id)
        self.cur.execute(sql, data)
        self.conn.commit()
        return self.get_user_by_id(user_id)

db = Database()