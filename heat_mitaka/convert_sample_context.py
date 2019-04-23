import ast
import json

class RequestContext(object):
    def __init__(self):
        with open("sample_context.txt", 'r') as sample_file:
            self.context = ast.literal_eval(sample_file.read())

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

def convert(context):
    with open("sample_json.txt", 'w') as sample_json:
        credentials = context.to_dict()
        buf = json.dumps(credentials["auth_token_info"], sort_keys=False, indent=4)
        sample_json.write(buf)
        print buf
    

if __name__ == "__main__":
    context = RequestContext()
    convert(context)