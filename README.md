# "OpenStack PolicyEngine疑似体験ツール" とは? ...
OpenStack基盤における権限設定/判定処理として、"oslo.policy"パッケージが活用されています.
https://github.com/openstack/oslo.policy

"policy.json"の挙動をオフラインで確認するツールです.
なお、ここでは、OpenStack基盤(Stein版)での動作を想定しております.

## ◼️ OpenStack基盤(heat)での、処理概要
OpenStack heatは、リクエストに応じて、適切なクラウドオペレーション（novaインスタンス作成など）を行います。

- heat-apiが、ユーザからのリクエストを受け付ける。
- heat-api内部で、必要なコンテキスト処理（token情報の入手等）を実施する。
- heat-api内部で、OpenStack固有の権限設定の記述に従って、実行可否を判定する。
- RabbitMQ等を介して、heat-engine側で適切なオーケストレーション処理を実施する。

![scope](images/Heat_architecture.png)

## ◼️ heat-api内部での権限判定の流れ
heatスタックを作成する場合だと、[StackControllerクラスのcreateメソッド](https://github.com/openstack/heat/blob/stable/stein/heat/api/openstack/v1/stacks.py#L398-L418)が起動される.

- [デコレータ"@util.registered_policy_enforce"](https://github.com/openstack/heat/blob/stable/stein/heat/api/openstack/v1/util.py#L32-L40)が起動される.
- [_policy_enforce"](https://github.com/openstack/heat/blob/stable/stein/heat/api/openstack/v1/util.py#L43-L57)が起動される.
- [req.context.policy.enforce](https://github.com/openstack/heat/blob/stable/stein/heat/api/openstack/v1/util.py#L48-L52)が起動される.
- ちなみに、[req.context.policy](https://github.com/openstack/heat/blob/stable/stein/heat/common/context.py#L117)の実態は、[policy.get_enforcer()](https://github.com/openstack/heat/blob/stable/stein/heat/common/context.py#L117)の戻り値、すなわち、[policy.Enforceクラス](https://github.com/openstack/heat/blob/stable/stein/heat/common/policy.py#L40-L118)である.
- [enforceメソッド](https://github.com/openstack/heat/blob/stable/stein/heat/common/policy.py#L92-L106)の中身は、こんな感じ.
```python
def enforce(self, context, action, scope=None, target=None,
            is_registered_policy=False):
    """Verifies that the action is valid on the target in this context.
       :param context: Heat request context
       :param action: String representing the action to be checked
       :param target: Dictionary representing the object of the action.
       :raises heat.common.exception.Forbidden: When permission is denied
               (or self.exc if supplied).
       :returns: A non-False value if access is allowed.
    """
    _action = '%s:%s' % (scope or self.scope, action)
    _target = target or {}
    return self._check(context, _action, _target, self.exc, action=action,
                       is_registered_policy=is_registered_policy)
```
- 続いて、[_checkメソッド](https://github.com/openstack/heat/blob/stable/stein/heat/common/policy.py#L64-L90)が起動されます.
- _checkメソッドの中身は、こんな感じ.
```python
def _check(self, context, rule, target, exc,
           is_registered_policy=False, *args, **kwargs):
    """Verifies that the action is valid on the target in this context.
       :param context: Heat request context
       :param rule: String representing the action to be checked
       :param target: Dictionary representing the object of the action.
       :raises heat.common.exception.Forbidden: When permission is denied
               (or self.exc if supplied).
       :returns: A non-False value if access is allowed.
    """
    do_raise = False if not exc else True
    credentials = context.to_policy_values()
    if is_registered_policy:
        try:
            return self.enforcer.authorize(rule, target, credentials,
                                           do_raise=do_raise,
                                           exc=exc, action=rule)
        except policy.PolicyNotRegistered:
            if self.log_not_registered:
                with excutils.save_and_reraise_exception():
                    LOG.exception(_('Policy not registered.'))
            else:
                raise
    else:
        return self.enforcer.enforce(rule, target, credentials,
                                     do_raise, exc=exc, *args, **kwargs)
```
- "oslo.policy"パッケージで定義された[Enforcerクラスのenforceメソッド](https://github.com/openstack/oslo.policy/blob/stable/stein/oslo_policy/policy.py#L819-L975)が起動される.
- このあと、"policy.json"の権限設定とコンテキスト情報を比較判定する.
- 判定結果"allowed"が、"True"の場合には、[createメソッド](https://github.com/openstack/heat/blob/stable/stein/heat/api/openstack/v1/util.py#L48-L55)が起動される.

## ◼️ Policy Engine疑似体験ツールの概要
コンテキスト情報を事前にサンプルとして準備しておいて、Policy Engineを呼び出して、権限判定の結果をオフラインで確認するツールになります.
ちなみに、コンテキスト情報の入手は、OpenStack(Mitaka版)の環境を使用して取得しました.
従って、厳密に、Stein版OpenStack Policy Engineを模擬していない可能性があります.


### (1) ツール環境整備
手っ取り早く、動作環境を整えるため、dockerコンテナを活用します.
```
$ docker build -t offline_policy_checker .
$ docker run -it offline_policy_checker bash
```

### (2) 起動してみる
dockerコンテナを起動して、OpenStack権限設定/判定処理を疑似体験してみましょう.

#### (2-1) Heat(Stein版)での権限設定/判定処理の疑似体験
- まずは、シンプルに疑似体験ツールを起動してみます.

```
root@48bb11d7bcd8:~# cd heat_stein
```
```
root@119108a5b344:~/heat_stein# python offline_policy_checker.py
------------------------------------------------------------
Checking result: action=[create], allowed=[True]
------------------------------------------------------------
```
- 続いて、事前に準備したコンテキスト情報の内容を確認しつつ、"index"アクション時の権限設定/判定処理を確認します.

```
root@119108a5b344:~/heat_stein# python offline_policy_checker.py --action index --debug
{
    "username": null,
    "project_domain_id": "default",
    "user_id": "8880f4a4bee844f48d93fa2d3c9a0b1b",
    "show_deleted": false,
    "roles": [
        "_member_",
        "heat_stack_owner"
    ],
    "user_identity": "8880f4a4bee844f48d93fa2d3c9a0b1b 30f8255b1c10422daa5fcf9f08e12243",
    "tenant_id": "30f8255b1c10422daa5fcf9f08e12243",
    "auth_token": "2004d1801bb645cf91b015c2a97579ed",
    "user_domain_id": "default",
    "auth_token_info": {
        "token": {
            "methods": [
                "password",
                "token"
            ],
            "roles": [
                {
                    "id": "9fe2ff9ee4384b1894a90878d3e92bab",
                    "name": "_member_"
                },
                {
                    "id": "502393bd5c2845b191146c41f5413cb7",
                    "name": "heat_stack_owner"
                }
            ],
            "auth_token": "2004d1801bb645cf91b015c2a97579ed",
            "expires_at": "2019-04-18T09:35:33.000000Z",
            "project": {
                "domain": {
                    "id": "default",
                    "name": "Default"
                },
                "id": "30f8255b1c10422daa5fcf9f08e12243",
                "name": "demo"
            },

... (snip)

        }
    },
    "auth_url": "http://10.79.5.191:35357/v3/",
    "trust_id": null,
    "request_id": "req-943e2a8c-845f-4c62-bddb-dc83374e526a",
    "is_admin": false,
    "trustor_user_id": null,
    "password": null,
    "aws_creds": null,
    "region_name": null,
    "tenant": "demo",
    "user": null
}
------------------------------------------------------------
Checking result: action=[index], allowed=[True]
------------------------------------------------------------
```

#### (2-2) Nova(Stein版)でのPolicy権限設定/判定処理の疑似体験

- こちらも、まずは、シンプルに疑似体験ツールを起動してみます.

```
root@119108a5b344:~# cd nova_stein
```
```
root@119108a5b344:~/nova_stein# python offline_policy_checker.py
------------------------------------------------------------
Checking result: action=[reboot], result=[True]
------------------------------------------------------------
```
- 続いて、事前に準備したコンテキスト情報の内容を確認しつつ、"attach_interface"アクション時の権限設定/判定処理を確認します.

```
root@119108a5b344:~/nova_stein# python offline_policy_checker.py --action attach_interface --debug
{
    "project_name": null,
    "user_id": null,
    "quota_class": null,
    "service_catalog": [],
    "request_id": "req-27a1a9c7-5eed-492f-983f-94778ad9dec8",
    "is_admin": true,
    "project_id": null,
    "user_name": null,
    "remote_address": null,
    "read_deleted": "no"
}
------------------------------------------------------------
Checking result: action=[attach_interface], result=[True]
------------------------------------------------------------
```
