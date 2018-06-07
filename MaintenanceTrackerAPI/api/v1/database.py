import os

import psycopg2


class Database:
    def __init__(self,
                 db: str = os.getenv('DB_NAME'),
                 user: str = os.getenv('DB_USER'),
                 password: str = os.getenv('DB_PASSWORD')):

        self.conn = psycopg2.connect(database=db,
                                     user=user,
                                     password=password)
        self.cur = None

    def query(self, query):
        self.cur = self.conn.cursor()
        try:
            self.cur.execute(query)
        except Exception as e:
            self.cur.connection.rollback()
            return e.args[0]

    def close(self):
        self.cur.close()
        self.conn.close()

    def create_all(self):
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
        self.query("drop table if exists requests;")
        self.query("drop table if exists users;")
        self.query("drop table if exists tokens;")
        self.conn.commit()

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
        query = 'select * from requests;'
        self.query(query)
        requests = self.cur.fetchall()
        if not requests:
            return
        return_list = []
        for a_request in requests:
            request_dict = dict(
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
        sql = 'select * from requests where id=%s;'
        data = (request_id,)
        self.cur = self.conn.cursor()
        self.cur.execute(sql, data)
        requests = self.cur.fetchall()
        if not requests:
            return
        a_request = requests[0]
        request_dict = dict(
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
