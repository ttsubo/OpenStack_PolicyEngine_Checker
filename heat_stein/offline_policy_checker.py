import ast
import json
from oslo_config import cfg
from oslo_policy import policy

CONF = cfg.CONF

CONF.register_cli_opts([
    cfg.StrOpt('action', default="create",
               help='please set action'),
    cfg.BoolOpt('debug', default=False,
               help='please set debug mode'),
])
CONF(project='heat', prog='offline_policy_checker.py')

REQUEST_SCOPE = 'stacks'
DEFAULT_RULES = policy.Rules.from_dict({'default': '!'})
DEFAULT_RESOURCE_RULES = policy.Rules.from_dict({'default': '@'})
ENFORCER = None

def get_enforcer():
    global ENFORCER
    if ENFORCER is None:
        ENFORCER = Enforcer()
    return ENFORCER

class Forbidden(Exception):
    msg_fmt = "You are not authorized to use %(action)s."

    def __init__(self, action='this action'):
        super(Forbidden, self).__init__(action=action)

class RequestContext(object):
    def __init__(self):
        with open("sample_context.txt", 'r') as sample_file:
            self.context = ast.literal_eval(sample_file.read())
        self.policy = get_enforcer()

    def to_dict(self):
        return {
            "auth_token": self.context["auth_token"],
            "username": self.context["username"],
            "user_id": self.context["user_id"],
            "password": self.context["password"],
            "aws_creds": self.context["aws_creds"],
            "tenant": self.context["tenant"],
            "tenant_id": self.context["tenant_id"],
            "trust_id": self.context["trust_id"],
            "trustor_user_id": self.context["trustor_user_id"],
            "auth_token_info": self.context["auth_token_info"],
            "auth_url": self.context["auth_url"],
            "roles": self.context["roles"],
            "is_admin": self.context["is_admin"],
            "user": self.context["user"],
            "request_id": self.context["request_id"],
            "show_deleted": self.context["show_deleted"],
            "region_name": self.context["region_name"],
            "user_identity": self.context["user_identity"],
            "user_domain_id": self.context["user_domain_id"],
            "project_domain_id": self.context["project_domain_id"],
        }


class Enforcer(object):
    def __init__(self, scope='heat', exc=Forbidden,
                 default_rule=DEFAULT_RULES['default'], policy_file=None):
        self.scope = scope
        self.exc = exc
        self.enforcer = policy.Enforcer(
            CONF, default_rule=default_rule, policy_file=policy_file)

    def _check(self, context, rule, target, exc,
               is_registered_policy=False, *args, **kwargs):
        do_raise = False if not exc else True
        credentials = context.to_dict()
        if CONF.debug is True:
            print(json.dumps(credentials, sort_keys=False, indent=4))
        return self.enforcer.enforce(rule, target, credentials,
                                     do_raise, exc=exc, *args, **kwargs)

    def enforce(self, context, action, scope=None, target=None,
                is_registered_policy=False):
        _action = '%s:%s' % (scope or self.scope, action)
        _target = target or {}
        return self._check(context, _action, _target, self.exc, action=action,
                           is_registered_policy=is_registered_policy)


if __name__ == "__main__":
    context = RequestContext()

    try:
        allowed = context.policy.enforce(context=context, action=CONF.action,
                                         scope=REQUEST_SCOPE, is_registered_policy=False)
    except Exception as e:
        print(e)
        allowed = False
    print "-" * 60
    print("Checking result: action=[{0}], allowed=[{1}]".format(CONF.action, allowed))
    print "-" * 60
