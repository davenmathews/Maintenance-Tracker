from flask_login import LoginManager, current_user
from flask_restplus import Resource, fields
from flask_restplus.namespace import Namespace

from MaintenanceTrackerAPI.api.v1.boilerplate import extract_from_payload, \
    get_validated_payload
from MaintenanceTrackerAPI.api.v1.exceptions import PayloadExtractionError

auth_ns = Namespace('auth')

login_manager = LoginManager()

user_login_model = auth_ns.model('user_login_model', {
    'email': fields.String(title='Your email address', required=True,
                           example='myemail@company.com'),
    'password': fields.String(title='Your email address', required=True,
                              example='password.Pa55word')
})


class Login(Resource):
    @auth_ns.expect(user_login_model)
    @auth_ns.response(200, 'user logged in successfully')
    @auth_ns.response(415, 'request data not in json format')
    @auth_ns.response(401, 'invalid password')
    @auth_ns.response(400, 'bad request')
    def post(self):
        """
        User Login

        Makes use of Flask-Login

        Use the correct user information to login. Guidelines as stipulated
        in the register route should be followed

        Note: Only one user can be logged in per client

        """
        try:
            return {'message': current_user.email + ' is currently logged in'}, \
                   400
        except AttributeError:
            pass

        email, password = None, None
        try:
            payload = get_validated_payload(self)
            list_of_names = ['email', 'password']
            email, password = extract_from_payload(payload, list_of_names)
        except PayloadExtractionError as e:
            auth_ns.abort(e.abort_code, e.msg)

        pass
