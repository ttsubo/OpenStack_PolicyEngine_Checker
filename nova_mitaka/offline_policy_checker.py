import ast
import json
from oslo_config import cfg
from oslo_policy import policy

CONF = cfg.CONF
_ENFORCER = None

CONF.register_cli_opts([
    cfg.StrOpt('action', default="reboot",
               help='please set action'),
    cfg.BoolOpt('debug', default=False,
               help='please set debug mode'),
])
CONF(project='nova', prog='offline_policy_checker.py')


class PolicyNotAuthorized(Exception):
    msg_fmt = "Policy doesn't allow %(action)s to be performed."

class RequestContext(object):
    def __init__(self):
        with open("sample_context.txt", 'r') as sample_file:
            self.context = ast.literal_eval(sample_file.read())

    def to_dict(self):
        return {
            "user_id": self.context["user_id"],
            "project_id": self.context["project_id"],
            "is_admin": self.context["is_admin"],
            "read_deleted": self.context["read_deleted"],
            "roles": self.context["roles"],
            "remote_address": self.context["remote_address"],
            "request_id": self.context["request_id"],
            "quota_class": self.context["quota_class"],
            "user_name": self.context["user_name"],
            "service_catalog": self.context["service_catalog"],
            "project_name": self.context["project_name"],
            "instance_lock_checked": self.context["instance_lock_checked"],
        }

def init(policy_file=None, rules=None, default_rule=None, use_conf=True):
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF,
                                    policy_file=policy_file,
                                    rules=rules,
                                    default_rule=default_rule,
                                    use_conf=use_conf)

def enforce(context, action, target, exc=None):
    init()
    credentials = context.to_dict()
    if CONF.debug == True:
        print(json.dumps(credentials, sort_keys=False, indent=4))
    if not exc:
        exc = PolicyNotAuthorized
    try:
        result = _ENFORCER.enforce(action, target, credentials,
                                   do_raise=False, exc=exc, action=action)
    except Exception:
        print('Policy check for %(action)s failed with credentials '
              '%(credentials)s',
              {'action': action, 'credentials': credentials})
        result = False
    return result


if __name__ == "__main__":
    context = RequestContext()
    scope = 'compute'
    target = {}
    _action = '%s:%s' % (scope, CONF.action)
    result = enforce(context, _action, target)

    print "-" * 60
    print("Checking result: action=[{0}], result=[{1}]".format(CONF.action, result))
    print "-" * 60
